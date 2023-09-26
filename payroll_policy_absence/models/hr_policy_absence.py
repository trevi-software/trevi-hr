# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PolicyAbsence(models.Model):

    _name = "hr.policy.absence"
    _description = "Absence payroll policy"
    _order = "date desc"

    name = fields.Char(size=128, required=True)
    date = fields.Date(string="Effective Date", required=True)
    line_ids = fields.One2many(
        string="Policy Lines",
        comodel_name="hr.policy.line.absence",
        inverse_name="policy_id",
    )

    def get_codes(self):

        res = []
        for policy in self:
            [
                res.append((line.code, line.name, line.type, line.rate, line.use_awol))
                for line in policy.line_ids
            ]
        return res

    def paid_codes(self):

        res = {}
        for policy in self:
            res[policy.id] = []
            [
                res[policy.id].append((line.code, line.name))
                for line in policy.line_ids
                if line.type == "paid"
            ]
        return res

    def unpaid_codes(self):

        res = {}
        for policy in self:
            res[policy.id] = []
            [
                res[policy.id].append((line.code, line.name))
                for line in policy.line_ids
                if line.type == "unpaid"
            ]
        return res
