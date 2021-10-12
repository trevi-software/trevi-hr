# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class EnrollEmployee(models.TransientModel):

    _name = "hr.benefit.enroll.employee"
    _description = "Employee Benefit Enrollment Form"

    benefit_id = fields.Many2one(
        string="Benefit",
        comodel_name="hr.benefit",
        required=True,
        default=lambda self: self._get_benefit(),
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee", required=True
    )
    start_date = fields.Date(
        string="Enrollment Date", required=True, default=fields.Date.today()
    )
    end_date = fields.Date(string="Termination Date")

    @api.model
    def _get_benefit(self):

        if self.env.context is None:
            self.env.with_context({})
        return self.env.context.get("active_id", False)

    def do_enroll(self):

        if not self.benefit_id or not self.employee_id:
            return {"type": "ir.actions.act_window_close"}

        vals = {
            "benefit_id": self.benefit_id.id,
            "employee_id": self.employee_id.id,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
        self.env["hr.benefit.policy"].create(vals)

        return {"type": "ir.actions.act_window_close"}
