# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PolicyPresence(models.Model):

    _name = "hr.policy.presence"
    _description = "Presence payroll policy"
    _order = "date desc"

    name = fields.Char(required=True)
    date = fields.Date(string="Effective Date", required=True)
    work_hours_per_week = fields.Integer(
        string="Working Hours/Week", required=True, default=40
    )
    work_days_per_week = fields.Integer(
        string="Work Days/Week", default=6, help="Regular work days in a work week."
    )
    line_ids = fields.One2many(
        string="Policy Lines",
        comodel_name="hr.policy.line.presence",
        inverse_name="policy_id",
    )

    def get_codes(self):

        res = []
        for policy in self:
            for line in policy.line_ids:
                res.append(
                    (
                        line.code,
                        line.name,
                        line.type,
                        line.rate,
                        line.duration,
                        line.accrual_policy_line_id.id,
                        line.accrual_policy_line_id.code,
                        line.accrual_policy_line_id.accrual_rate_hour,
                        line.accrual_min,
                        line.accrual_max,
                    )
                )
        return res
