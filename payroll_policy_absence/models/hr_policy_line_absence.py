# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PolicyLineAbsence(models.Model):

    _name = "hr.policy.line.absence"
    _description = "Absence payroll policy line"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Use this code in the salary rules.")
    holiday_status_id = fields.Many2one(
        comodel_name="hr.leave.type", string="Leave", required=True
    )
    policy_id = fields.Many2one(comodel_name="hr.policy.absence", string="Policy")
    type = fields.Selection(
        selection=[("paid", "Paid"), ("unpaid", "Unpaid"), ("dock", "Dock")],
        required=True,
        help="Determines how the absence will be treated in payroll."
        " The 'Dock Salary' type will deduct money (usefull for salaried employees).",
    )
    rate = fields.Float(required=True, default=1.0, help="Multiplier of employee wage.")
    use_awol = fields.Boolean(
        string="Absent Without Leave",
        help="Use this policy to record employee time absence not covered by other leaves.",
    )

    @api.onchange("holiday_status_id")
    def onchange_holiday(self):

        if self.holiday_status_id:
            self.name = self.holiday_status_id.name
            self.code = self.holiday_status_id.code
