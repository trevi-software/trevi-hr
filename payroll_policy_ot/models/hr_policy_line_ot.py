# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from pytz import common_timezones

from odoo import api, fields, models


class PolicyLineOt(models.Model):

    _name = "hr.policy.line.ot"
    _description = "Over-time payroll policy line"

    @api.model
    def _tz_list(self):

        res = tuple()
        for name in common_timezones:
            res += ((name, name),)
        return res

    name = fields.Char(size=64, required=True)
    policy_id = fields.Many2one(comodel_name="hr.policy.ot", string="Policy")
    type = fields.Selection(
        selection=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("restday", "Rest Day"),
            ("holiday", "Public Holiday"),
        ],
        required=True,
    )
    weekly_working_days = fields.Integer()
    active_after = fields.Integer(help="Minutes after which this policy applies")
    active_start_time = fields.Char(size=5, help="Time in 24 hour time format")
    active_end_time = fields.Char(size=5, help="Time in 24 hour time format")
    tz = fields.Selection(selection=_tz_list, string="Time Zone")
    rate = fields.Float(required=True, default=1, help="Multiplier of employee wage.")
    accrual_policy_line_id = fields.Many2one(
        string="Accrual Policy Line", comodel_name="hr.policy.line.accrual"
    )
    accrual_rate = fields.Float(digits="Accruals")
    accrual_min = fields.Float(string="Minimum Accrual", digits="Accruals")
    accrual_max = fields.Float(string="Maximum Accrual", digits="Accruals")
    code = fields.Char(required=True, help="Use this code in the salary rules.")
