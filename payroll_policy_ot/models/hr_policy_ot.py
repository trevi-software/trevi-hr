# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PolicyOt(models.Model):

    _name = "hr.policy.ot"
    _description = "Over-time payroll policy"
    _order = "date desc"

    name = fields.Char(size=128, required=True)
    date = fields.Date(string="Effective Date", required=True)
    line_ids = fields.One2many(
        string="Policy Lines",
        comodel_name="hr.policy.line.ot",
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
                        line.accrual_policy_line_id.id,
                        line.accrual_policy_line_id.code,
                        line.accrual_rate,
                        line.accrual_min,
                        line.accrual_max,
                    )
                )
        return res

    def daily_codes(self):

        res = []
        for policy in self:
            for line in policy.line_ids:
                if line.type == "daily":
                    res.append((line.code, line.name))
        return res

    def restday_codes(self):

        res = []
        for policy in self:
            for line in policy.line_ids:
                if line.type == "weekly" and line.weekly_working_days > 0:
                    res.append((line.code, line.name))
        return res

    def restday2_codes(self):

        res = []
        for policy in self:
            for line in policy.line_ids:
                if line.type == "restday":
                    res.append((line.code, line.name))
        return res

    def weekly_codes(self):

        res = []
        for policy in self:
            for line in policy.line_ids:
                if line.type == "weekly" and line.weekly_working_days > 0:
                    res.append((line.code, line.name))
        return res

    def holiday_codes(self):

        res = []
        for policy in self:
            for line in policy.line_ids:
                if line.type == "holiday":
                    res.append((line.code, line.name))
        return res
