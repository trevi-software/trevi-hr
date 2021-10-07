# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
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
        states={"draft": [("readonly", False)]},
    )
    reason_id = fields.Many2one(
        string="Reason",
        comodel_name="hr.employee.termination.reason",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    notes = fields.Text(readonly=True, states={"draft": [("readonly", False)]})
    employee_id = fields.Many2one(
        string="Employee", comodel_name="hr.employee", required=True, readonly=True
    )
    department_id = fields.Many2one(
        string="Department",
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
        string="Company",
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

        return super(Separation, self)._track_subtype(init_values)

    @api.model
    def create(self, vals):
        res = super(Separation, self).create(vals)
        res.employee_state = res.employee_id.status
        res.employee_id.set_state_separation()
        if res.employee_id.contract_id:
            c = res.employee_id.contract_id
            res.contract_date_end = c.date_end
            c.date_end = res.name
        return res

    def unlink(self):

        for term in self:
            if term.state == "done":
                raise UserError(
                    _(
                        "Unable to delete record!"
                        "Employment separation already completed."
                    )
                )

            # Trigger employee status change back to Active
            term.employee_id.set_state_active(term.employee_state)

        return super(Separation, self).unlink()

    def signal_cancel(self):

        for term in self:

            # Trigger a status change of the employee and his contract(s)
            term.employee_id.set_state_active(term.employee_state)

            term.state = "cancel"

        return True

    def effective_date_in_future(self):

        self.ensure_one()
        if self.name <= datetime.now().date():
            return False

        return True

    def signal_done(self):

        for term in self:
            if term.effective_date_in_future():
                raise UserError(
                    _(
                        "Unable to deactivate employee!"
                        "Effective date is still in the future. Change the date \
                      and try again"
                    )
                )

            # Trigger a status change of the employee and any contracts pending termination.
            term.employee_id.set_state_inactive()
            term.employee_id.contract_id.state = "close"
            term.employee_id.contract_ids.write({"active": False})
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
                    fields.Date.to_string(date.today() + relativedelta(days=1)),
                ),
            ]
        )
        if len(separations) > 0:
            employees = separations.mapped("employee_id")
            employees.set_state_inactive()
            employees.mapped("contract_id").write({"state": "close"})
            separations.write({"state": "done"})
