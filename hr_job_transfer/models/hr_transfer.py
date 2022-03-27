# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class HrTransfer(models.Model):
    _name = "hr.department.transfer"
    _inherit = ["mail.thread"]
    _description = "Departmental Transfer"
    _rec_name = "date"
    _check_company_auto = True

    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    src_id = fields.Many2one(
        string="From",
        comodel_name="hr.job",
        compute="_compute_onchange_employee",
        store=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    dst_id = fields.Many2one(
        string="Destination",
        comodel_name="hr.job",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    src_department_id = fields.Many2one(
        string="From Department",
        related="src_id.department_id",
        comodel_name="hr.department",
        store=True,
        readonly=True,
    )
    dst_department_id = fields.Many2one(
        string="Destination Department",
        related="dst_id.department_id",
        comodel_name="hr.department",
        store=True,
        readonly=True,
        check_company=True,
    )
    src_contract_id = fields.Many2one(
        string="From Contract",
        comodel_name="hr.contract",
        compute="_compute_onchange_employee",
        store=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    dst_contract_id = fields.Many2one(
        string="Destination Contract",
        comodel_name="hr.contract",
        readonly=True,
        check_company=True,
    )
    date = fields.Date(
        string="Effective Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("pending", "Pending"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        readonly=True,
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
        store=True,
        readonly=True,
    )

    @api.depends("employee_id")
    def _compute_onchange_employee(self):

        for transfer in self:
            if transfer.employee_id:
                transfer.src_id = transfer.employee_id.job_id
                transfer.src_contract_id = transfer.employee_id.contract_id
            else:
                transfer.src_id = False
                transfer.src_contract_id = False

    def _track_subtype(self, init_values):

        self.ensure_one()

        if "state" in init_values:
            if self.state == "confirm":
                return self.env.ref("hr_job_transfer.mt_alert_xfer_confirmed")
            elif self.state == "pending":
                return self.env.ref("hr_job_transfer.mt_alert_xfer_pending")
            elif self.state == "done":
                return self.env.ref("hr_job_transfer.mt_alert_xfer_done")

        return super(HrTransfer, self)._track_subtype(init_values)

    def effective_date_in_future(self):

        for transfer in self:
            if transfer.date <= fields.Date.today():
                return False
        return True

    def unlink(self):

        if not self.env.context.get("force_delete", False):
            for transfer in self:
                if transfer.state not in ["draft"]:
                    raise UserError(
                        _(
                            "Unable to Delete Transfer!\n"
                            "Transfer has been initiated. Either cancel the transfer or\n"
                            "create another transfer to undo it."
                        )
                    )
        return super(HrTransfer, self).unlink()

    def action_transfer(self):

        self.ensure_one()
        has_permission = self._check_permission_group(
            "hr_job_transfer.group_hr_transfer"
        )
        if has_permission and not self.effective_date_in_future():
            self.state_done()
        else:
            self.write({"state": "pending"})

    def action_confirm(self):

        self.ensure_one()
        has_permission = self._check_permission_group(
            "hr_job_transfer.group_hr_transfer"
        )
        if has_permission:
            self.signal_confirm()

    def action_cancel(self):

        self.ensure_one()
        has_permission = self._check_permission_group(
            "hr_job_transfer.group_hr_transfer"
        )
        if has_permission:
            self.write({"state": "cancel"})

    @api.model
    def _check_state(self, contract, effective_date):

        _state_kanban_state = [
            ("trial", "normal"),
            ("trial", "blocked"),
            ("open", "normal"),
            ("open", "blocked"),
        ]

        if (contract.state, contract.kanban_state) not in _state_kanban_state:
            raise UserError(
                _(
                    "Warning!\n"
                    "The current state of the contract does not permit changes."
                )
            )

        if contract.date_end and effective_date >= contract.date_end:
            raise UserError(
                _(
                    "Warning!\n"
                    "The contract end date is on or before the effective date of the transfer."
                )
            )

        return True

    def _check_permission_group(self, group=None):

        for transfer in self:
            if group and not transfer.user_has_groups(group):
                raise AccessError(
                    _("You don't have the access rights to take this action.")
                )
            else:
                continue
        return True

    @api.model
    def transfer_contract(self, contract, job, transfer, effective_date):

        Contract = self.env["hr.contract"]

        # If the start and date is the same as the contract start date simply change
        # the current contract.
        if effective_date == contract.date_start:
            contract.job_id = job
            # Link to the new contract
            transfer.dst_contract_id = contract
            return

        # generate unique contract name as it is a required field.
        emp_contract_count = self.env["hr.contract"].search_count(
            [("employee_id", "=", contract.employee_id.id)]
        )
        _contract_name = _(
            "%s's Contract [%d]", contract.employee_id.name, (emp_contract_count + 1)
        )

        # Copy the contract and adjust start/end dates, job id, etc. accordingly.
        default = {
            "job_id": job.id,
            "date_start": effective_date,
            "name": _contract_name,
            "state": False,
            "message_ids": False,
            "trial_date_start": contract.trial_date_start,
            "trial_date_end": contract.trial_date_end,
        }
        data = contract.copy_data(default=default)

        # Terminate the current contract (and trigger appropriate state change)
        contract.date_end = effective_date - relativedelta(days=1)
        contract.signal_close()

        # create new contract
        new_contract = Contract.create(data)

        if new_contract:
            # Set the new contract to the appropriate state
            new_contract.signal_confirm()

            # Link to the new contract
            transfer.dst_contract_id = new_contract

        return True

    def state_confirm(self):

        for transfer in self:
            self._check_state(transfer.src_contract_id, transfer.date)
            transfer.state = "confirm"

        return True

    def state_done(self):

        today = fields.Date.today()

        for transfer in self:
            if transfer.date <= today:
                self._check_state(transfer.src_contract_id, transfer.date)
                transfer.employee_id.department_id = transfer.dst_department_id
                self.transfer_contract(
                    transfer.src_contract_id,
                    transfer.dst_id,
                    transfer,
                    transfer.date,
                )
                transfer.state = "done"
            else:
                return False

        return True

    def signal_confirm(self):

        for transfer in self:
            self._check_state(transfer.src_contract_id, transfer.date)
            # If the user is a member of 'approval' group, go straight to 'approval'
            if (
                self.user_has_groups("hr_job_transfer.group_hr_transfer")
                and transfer.effective_date_in_future()
            ):
                transfer.state = "pending"
            else:
                transfer.state_confirm()

        return True

    @api.model
    def try_pending_department_transfers(self):
        """Completes pending departmental transfers. Called from the scheduler."""

        self._check_permission_group("hr_job_transfer.group_hr_transfer")

        Transfer = self.env["hr.department.transfer"]
        pending_transfers = Transfer.search(
            [("state", "=", "pending"), ("date", "<=", fields.Date.today())]
        )

        for transfer in pending_transfers:
            transfer.state_done()

        return True
