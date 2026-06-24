# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import math

from odoo import fields, models


class BenefitPolicy(models.Model):

    _inherit = "hr.benefit.policy"

    premium_payment_ids = fields.One2many(
        string="Premium Payments",
        comodel_name="hr.benefit.premium.payment",
        inverse_name="policy_id",
        readonly=True,
    )

    def calculate_advantage(self, dE):

        self.ensure_one()
        adv_amount = 0
        adv = self.benefit_id.get_latest_advantage(dE)
        if self.advantage_override:
            adv_amount = self.advantage_amount
        elif adv:
            if adv.type == "allowance":
                adv_amount = adv.allowance_amount
            elif adv.type == "loan":
                adv_amount = adv.loan_amount
        return adv_amount

    def _get_paid_amount(self):

        self.ensure_one()
        res = 0
        for payment in self.premium_payment_ids:
            if payment.state not in ["draft", "cancel"]:
                res += payment.amount
        return res

    def calculate_premium(self, dE, annual_pay_periods, refund=False):

        self.ensure_one()
        prm_amount = 0
        prm = self.benefit_id.get_latest_premium(dE)
        paid = self._get_paid_amount()
        if refund:
            payments = self.premium_payment_ids.filtered(
                lambda r: r.date <= dE and r.state not in ["draft", "cancel"]
            ).sorted("date")
            prm_amount = len(payments) > 0 and payments[-1].amount or 0
        elif self.premium_override:
            total = self.premium_override_total
            prm_amount = self.premium_override_amount
            if total:
                prm_amount = (
                    (total - paid) > prm_amount and prm_amount or (total - paid)
                )
                if prm_amount < 0:
                    prm_amount = 0
        elif prm:
            if prm.type == "annual":
                prm_amount = math.floor(prm.amount / float(annual_pay_periods))
            else:
                prm_amount = math.floor(prm.amount / float(annual_pay_periods / 12))
            if prm.total_amount and (prm.total_amount - paid) < prm_amount:
                prm_amount = (
                    (prm.total_amount - paid) > 0 and (prm.total_amount - paid) or 0
                )
        return prm_amount
