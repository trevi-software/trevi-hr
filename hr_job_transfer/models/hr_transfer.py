# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class HrTransfer(models.Model):
    _name = "hr.department.transfer"
    _inherit = ["mail.thread"]  # noqa: RUF012
    _description = "Departmental Transfer"
    _rec_name = "date"
    _check_company_auto = True

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        required=True,
        check_company=True,
    )
    src_id = fields.Many2one(
        string="From",
        comodel_name="hr.job",
        compute="_compute_onchange_employee",
        store=True,
        readonly=True,
        check_company=True,
    )
    dst_id = fields.Many2one(
        string="Destination",
        comodel_name="hr.job",
        required=True,
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
        comodel_name="hr.version",
        compute="_compute_onchange_employee",
        store=True,
        readonly=True,
        check_company=True,
    )
    dst_contract_id = fields.Many2one(
        string="Destination Contract",
        comodel_name="hr.version",
        readonly=True,
        check_company=True,
    )
    date = fields.Date(
        string="Effective Date",
        required=True,
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
                transfer.src_contract_id = transfer.employee_id.version_id
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

        return super()._track_subtype(init_values)

    def effective_date_in_future(self):
        for transfer in self:
            if transfer.date <= fields.Date.today():
                return False
        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_except_not_draft(self):
        # ``force_delete`` must not be honoured for anyone who can simply put
        # it in the context: an HR user with delete access could otherwise
        # erase a confirmed or completed transfer. Only a trusted
        # administrative caller may bypass the draft-only guard.
        force_delete = (
            self.env.context.get("force_delete", False) and self.env.is_admin()
        )
        if not force_delete:
            for transfer in self:
                if transfer.state not in ["draft"]:
                    raise UserError(
                        self.env._(
                            "Unable to Delete Transfer!\n"
                            "Transfer has been initiated. Either cancel the "
                            "transfer or\n"
                            "create another transfer to undo it."
                        )
                    )

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
        """Reject a transfer whose source contract is not a running version.

        Odoo 19 dropped ``hr.contract`` (and with it trevi's custom
        ``state``/``kanban_state`` machine), so a contract is now an
        ``hr.version``. The 18.0 ("trial"/"open") check is expressed with the
        native flags: the version must be active, started, and neither past
        nor future.
        """
        if (
            not contract.active
            or not contract.contract_date_start
            or contract.is_past
            or contract.is_future
        ):
            raise UserError(
                self.env._(
                    "Warning!\n"
                    "The current state of the contract does not permit changes."
                )
            )

        if contract.contract_date_end and effective_date >= contract.contract_date_end:
            raise UserError(
                self.env._(
                    "Warning!\n"
                    "The contract end date is on or before the effective date "
                    "of the transfer."
                )
            )

        return True

    def _check_permission_group(self, group=None):
        # Check against ``self.env.user`` instead of looping over ``self``: the
        # check must also hold for an empty recordset (``create`` and the
        # ``@api.model`` cron entry point), where the loop would never run and
        # silently pass.
        if group and not self.env.user.has_group(group):
            raise AccessError(
                self.env._("You don't have the access rights to take this action.")
            )
        return True

    @api.model_create_multi
    def create(self, vals_list):
        # The ``state`` field is read-only in the form, but ``create`` is not
        # otherwise restricted. Require the approval group to open a transfer
        # directly in a non-draft state.
        for vals in vals_list:
            if vals.get("state", "draft") != "draft":
                self._check_permission_group("hr_job_transfer.group_hr_transfer")
        return super().create(vals_list)

    def write(self, vals):
        # ``readonly`` only restricts the form, not ``write``. Guard the
        # approval state machine so an ordinary HR user cannot push a transfer
        # into ``pending`` and let the scheduled job complete it without
        # approval. The action methods and the scheduled job (root) keep the
        # same right, so their transitions are unaffected.
        if "state" in vals:
            self._check_permission_group("hr_job_transfer.group_hr_transfer")
        return super().write(vals)

    @api.model
    def transfer_contract(self, contract, job, transfer, effective_date):
        Contract = self.env["hr.version"]

        # If the start date is the same as the contract start date simply change
        # the current version.
        if effective_date == contract.contract_date_start:
            contract.job_id = job
            # Link to the new version
            transfer.dst_contract_id = contract
            return

        # generate unique version name as it is a required field.
        emp_contract_count = Contract.search_count(
            [("employee_id", "=", contract.employee_id.id)]
        )
        _contract_name = self.env._(
            "%(name)s's Contract [%(number)d]",
            name=contract.employee_id.name,
            number=(emp_contract_count + 1),
        )

        # Copy the version and adjust start/end dates, job id, etc. accordingly.
        default = {
            "job_id": job.id,
            "contract_date_start": effective_date,
            "date_version": effective_date,
            "name": _contract_name,
            "message_ids": False,
            "trial_date_start": contract.trial_date_start,
            "trial_date_end": contract.trial_date_end,
        }
        data = contract.copy_data(default=default)

        # End the current version the day before the effective date. In 18.0
        # this also flipped the contract's custom ``state`` to ``close``;
        # setting the native end date is the 19.0 replacement.
        contract.contract_date_end = effective_date - relativedelta(days=1)

        # create new version
        new_contract = Contract.create(data)

        if new_contract:
            # The new version is live by virtue of its dates, there is no
            # longer a ``signal_confirm()`` state to set.
            # Link to the new version
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
                self.env.user.has_group("hr_job_transfer.group_hr_transfer")
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
