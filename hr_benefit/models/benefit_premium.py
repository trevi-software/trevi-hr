# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import math

from odoo import _, api, fields, models


class BenefitPremium(models.Model):

    _name = "hr.benefit.premium"
    _description = "Employee Benefit Premium Policy Line"
    _rec_name = "effective_date"
    _order = "benefit_id,effective_date desc"
    _sql_constraints = [
        (
            "unique_date_benefit_id",
            "UNIQUE(effective_date,benefit_id)",
            _("Effective dates must be unique per premium in a benefit!"),
        )
    ]

    benefit_id = fields.Many2one(string="Benefit", comodel_name="hr.benefit")
    effective_date = fields.Date(required=True)
    type = fields.Selection(
        string="Premium Type",
        selection=[("monthly", "Monthly"), ("annual", "Annual")],
        required=True,
    )
    amount = fields.Float(string="Premium Amount", digits="Account")
    total_amount = fields.Float(string="Total", digits="Account")
    no_of_installments = fields.Integer(
        string="No. of Installments",
        compute="_compute_installments",
        store=True,
        default=0,
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        res = []
        for rec in self:
            res.append(
                (rec.id, "{} {}".format(rec.benefit_id.name, rec.effective_date))
            )
        return res

    @api.depends("amount", "total_amount")
    def _compute_installments(self):
        for prm in self:
            prm.no_of_installments = (
                (prm.amount > 0 and prm.total_amount > 0)
                and int(math.ceil(float(prm.total_amount) / float(prm.amount)))
                or 0
            )
