# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.addons.hr_benefit.tests import common as benefit_common


class TestBenefit(benefit_common.TestBenefitCommon):
    @classmethod
    def setUpClass(cls):
        super(TestBenefit, cls).setUpClass()

        cls.PremiumPayment = cls.env["hr.benefit.premium.payment"]

    def test_benefit_policy_allowance_default_amount(self):

        today = date.today()
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_earning(bn, start=today, allowance=1000)
        pol = self.create_policy(self.eeJohn, bn, start=today)
        pol.state_open()

        self.assertEqual(
            pol.calculate_advantage(today),
            1000,
            "Calculated advantage must be benefit amount.",
        )

    def test_benefit_policy_allowance_override_amount(self):

        today = date.today()
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_earning(bn, start=today, allowance=1000)
        pol = self.create_policy(self.eeJohn, bn, start=today, advantage=4400)
        pol.state_open()

        self.assertEqual(
            pol.calculate_advantage(today),
            4400,
            "Calculated advantage must be override amount from policy.",
        )

    def test_benefit_policy_loan_amount(self):

        today = date.today()
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_earning(bn, start=today, ptype="loan", loan=15000)
        pol = self.create_policy(self.eeJohn, bn, start=today)
        pol.state_open()

        self.assertEqual(
            pol.calculate_advantage(today),
            15000,
            "Calculated loan amount must match amount from earning creation.",
        )

    def test_benefit_policy_first_premium(self):

        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn,
            date.today() - relativedelta(days=1),
            ptype="monthly",
            amount=100,
            total=300,
        )
        pol = self.create_policy(self.eeJohn, bn, date.today())

        self.assertEqual(
            100,
            pol.calculate_premium(date.today(), 12),
            "Initial premium amount and calculated premium should match",
        )

    def test_benefit_policy_last_premium(self):

        today = date.today()
        policy_start = today - relativedelta(days=4)
        dtPayment1 = today - relativedelta(days=3)
        dtPayment2 = today - relativedelta(days=2)
        dtPayment3 = today - relativedelta(days=1)
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn,
            date.today() - relativedelta(days=3),
            ptype="monthly",
            amount=100,
            total=340,
        )
        pol = self.create_policy(self.eeJohn, bn, policy_start)
        # Make first 3 payments (with one additional cancelled payment)
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment1, 12),
                "date": dtPayment1,
            }
        ).state_cancel()
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment1, 12),
                "date": dtPayment1,
            }
        ).state_done()
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment2, 12),
                "date": dtPayment2,
            }
        ).state_done()
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment3, 12),
                "date": dtPayment3,
            }
        ).state_done()

        self.assertEqual(
            len(pol.premium_payment_ids),
            4,
            "There should be 4 payments (including the cancelled one)",
        )
        self.assertEqual(
            40,
            pol.calculate_premium(today, 12),
            "The last payment must be the residual amount after previous payments",
        )

    def test_benefit_policy_premium_override(self):

        today = date.today()
        policy_start = today - relativedelta(days=4)
        dtPayment1 = today - relativedelta(days=3)
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn,
            date.today() - relativedelta(days=3),
            ptype="monthly",
            amount=100,
            total=340,
        )
        pol = self.create_policy(
            self.eeJohn, bn, policy_start, premium=200, premium_total=340
        )
        # Make first 1 payments (with one additional payment in 'draft')
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment1, 12),
                "date": dtPayment1,
            }
        )
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment1, 12),
                "date": dtPayment1,
            }
        ).state_done()

        self.assertEqual(
            len(pol.premium_payment_ids),
            2,
            "There should be 2 payments (including the 'draft' one)",
        )
        self.assertEqual(
            140,
            pol.calculate_premium(today, 12),
            "The last payment must be the residual amount after previous payments",
        )

    def test_benefit_policy_premium_refund(self):

        today = date.today()
        policy_start = today - relativedelta(days=4)
        dtPayment1 = today - relativedelta(days=3)
        dtPayment2 = today - relativedelta(days=2)
        dtPayment3 = today - relativedelta(days=1)
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn,
            policy_start,
            ptype="monthly",
            amount=100,
            total=340,
        )
        pol = self.create_policy(self.eeJohn, bn, policy_start)

        # Try to refund cancelled payment
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment1, 12),
                "date": dtPayment1,
            }
        ).state_cancel()
        self.assertEqual(
            0,
            pol.calculate_premium(today, 12, refund=True),
            "A Cancelled payment should not be refunded",
        )

        # Make all payments and try to refund last residual payment
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment1, 12),
                "date": dtPayment1,
            }
        ).state_done()
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment2, 12),
                "date": dtPayment2,
            }
        ).state_done()
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment3, 12),
                "date": dtPayment3,
            }
        ).state_done()
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": pol.id,
                "amount": pol.calculate_premium(dtPayment3, 12),
                "date": today,
            }
        ).state_done()
        self.assertEqual(
            40,
            pol.calculate_premium(today, 12, refund=True),
            "The premium to be refunded must be the last payment made",
        )
