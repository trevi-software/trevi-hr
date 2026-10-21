# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class SeparationReason(models.Model):
    _name = "hr.employee.termination.reason"
    _description = "Reason for Employee Separation"

    name = fields.Char(required=True)


class Separation(models.Model):
    _name = "hr.employee.termination"
    _inherit = ["mail.thread"]
    _description = "Data Related to Separation of Employee"

    name = fields.Date(
        string="Effective Date",
        required=True,
        readonly=True,
    )
    reason_id = fields.Many2one(
        comodel_name="hr.employee.termination.reason",
        required=True,
        readonly=True,
    )
    notes = fields.Text(readonly=True)
    employee_id = fields.Many2one(
        comodel_name="hr.employee", required=True, readonly=True
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        related="employee_id.department_id",
        store=True,
    )
    contract_date_end = fields.Date("Contract End Date")
    employee_state = fields.Char()
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("cancel", "Cancelled"),
            ("done", "Done"),
        ],
        tracking=True,
        default="draft",
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        groups="base.group_multi_company",
    )

    def _track_subtype(self, init_values):
        self.ensure_one()
        if "state" in init_values:
            if self.state == "confirm":
                return self.env.ref("hr_employee_status.mt_alert_state_confirm")
            elif self.state == "done":
                return self.env.ref("hr_employee_status.mt_alert_state_done")
            elif self.state == "cancel":
                return self.env.ref("hr_employee_status.mt_alert_state_cancel")

        return super()._track_subtype(init_values)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for res in records:
            res.employee_state = res.employee_id.status
            res.employee_id.set_state_separation()
            version = res.employee_id.version_id
            if version:
                # Keep the end date the contract had and end the contract on
                # the separation's effective date instead.
                res.contract_date_end = version.contract_date_end
                version.contract_date_end = res.name
        return records

    def _restore_contract_end_date(self):
        """Give the version back the end date it had before the separation."""
        for term in self:
            version = term.employee_id.version_id
            if version:
                version.contract_date_end = term.contract_date_end or False

        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done_separation(self):
        for term in self:
            if term.state == "done":
                raise UserError(
                    self.env._(
                        "Unable to delete record!"
                        "Employment separation already completed."
                    )
                )

    def unlink(self):
        for term in self:
            # Trigger employee status change back to Active
            term.employee_id.set_state_active(term.employee_state)
            term._restore_contract_end_date()

        return super().unlink()

    def signal_cancel(self):
        for term in self:
            # Trigger a status change of the employee and his contract
            term.employee_id.set_state_active(term.employee_state)
            term._restore_contract_end_date()

            term.state = "cancel"

        return True

    def effective_date_in_future(self):
        self.ensure_one()
        if self.name <= date.today():
            return False

        return True

    def signal_done(self):
        for term in self:
            if term.effective_date_in_future():
                raise UserError(
                    self.env._(
                        "Unable to deactivate employee!"
                        "Effective date is still in the future. Change the date \
                      and try again"
                    )
                )

            # Trigger a status change of the employee and end the contract at
            # the separation's effective date.
            version = term.employee_id.version_id
            term.employee_id.set_state_inactive()
            if version:
                version.signal_close(term.name)
            term.state = "done"

        return True

    @api.model
    def update_state(self):
        separations = self.search(
            [
                ("state", "=", "draft"),
                (
                    "name",
                    "<=",
                    date.today() + relativedelta(days=1),
                ),
            ]
        )
        if len(separations) > 0:
            employees = separations.mapped("employee_id")
            employees.set_state_inactive()
            for sep in separations:
                version = sep.employee_id.version_id
                if version:
                    version.signal_close(sep.name)
            separations.write({"state": "done"})
