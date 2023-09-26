# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PolicyLinePresence(models.Model):

    _name = "hr.policy.line.presence"
    _description = "Presence payroll policy line"

    name = fields.Char(size=64, required=True)
    policy_id = fields.Many2one(comodel_name="hr.policy.presence", string="Policy")
    code = fields.Char(required=True, help="Use this code in the salary rules.")
    rate = fields.Float(required=True, help="Multiplier of employee wage.", default=1.0)
    type = fields.Selection(
        selection=[
            ("normal", "Normal Working Hours"),
            ("holiday", "Holidays"),
            ("restday", "Rest Days"),
        ],
        required=True,
    )
    active_after = fields.Integer(
        required=True,
        help="Minutes after first punch of the day in which policy will take effect.",
    )
    duration = fields.Integer(required=True, help="In minutes.")
    accrual_policy_line_id = fields.Many2one(
        string="Accrual Policy Line", comodel_name="hr.policy.line.accrual"
    )
    accrual_min = fields.Float(string="Minimum Accrual", digits="Accruals")
    accrual_max = fields.Float(string="Maximum Accrual", digits="Accruals")
