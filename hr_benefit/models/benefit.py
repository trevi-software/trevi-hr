# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Benefit(models.Model):

    _name = "hr.benefit"
    _description = "Employee Benefit"
    _check_company_auto = True

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    has_premium = fields.Boolean()
    premium_ids = fields.One2many(
        string="Premiums", comodel_name="hr.benefit.premium", inverse_name="benefit_id"
    )
    has_advantage = fields.Boolean()
    advantage_ids = fields.One2many(
        string="Earnings",
        comodel_name="hr.benefit.advantage",
        inverse_name="benefit_id",
    )
    min_employed_days = fields.Integer(string="Minimum Employed Days", default=0)
    active = fields.Boolean(default=True)
    multi_policy = fields.Boolean(string="Multiple Policies/Employee", default=False)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    def name_get(self):

        res = []
        for rec in self:
            res.append((rec.id, "[%s] %s" % (rec.code, rec.name)))

        return res

    def _get_latest(self, dToday, ptype):
        """
        Return an advantage with an effective date before dToday but
        greater than all others.
        """

        if not self or not dToday:
            return None
        self.ensure_one()

        res = None
        line_ids = None
        if ptype == "advantage":
            line_ids = self.advantage_ids
        elif ptype == "premium":
            line_ids = self.premium_ids

        for line in line_ids:
            dLine = line.effective_date
            if dLine <= dToday:
                if res is None:
                    res = line
                elif dLine > res.effective_date:
                    res = line

        return res

    def get_latest_advantage(self, dToday):
        """
        Return an advantage with an effective date before dToday but
        greater than all others.
        """

        if not dToday:
            return None

        return self._get_latest(dToday, "advantage")

    def get_latest_premium(self, dToday):
        """Return a premium with an effective date before dToday but greater than all others"""

        if not dToday:
            return None

        return self._get_latest(dToday, "premium")
