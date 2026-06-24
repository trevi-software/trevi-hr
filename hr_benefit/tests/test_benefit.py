# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError

from . import common


class TestBenefit(common.TestBenefitCommon):
    def test_get_advantage_no_benefit(self):
        """#29 Try getting an advantage from an empty benefit recordset"""

        self.Benefit.get_latest_advantage(date.today())

    def test_get_premium_no_benefit(self):
        """#29 Try getting a premium from an empty benefit recordset"""

        self.Benefit.get_latest_premium(date.today())

    def test_get_latest_earning(self):
        """Get the earning with the latest effective date that is not in the future"""

        bn = self.create_benefit(self.benefit_create_vals)
        self.create_earning(bn, date.today() - relativedelta(days=1))
        earnToday = self.create_earning(bn, date.today())
        self.create_earning(bn, date.today() + relativedelta(days=1))
        latest = bn.get_latest_advantage(date.today())

        self.assertEqual(3, len(bn.advantage_ids))
        self.assertEqual(earnToday, latest)

    def test_get_latest_premium(self):
        """Get the premium with the latest effective date that is not in the future"""

        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(bn, date.today() - relativedelta(days=1))
        prmToday = self.create_premium(bn, date.today())
        self.create_premium(bn, date.today() + relativedelta(days=1))
        latest = bn.get_latest_premium(date.today())

        self.assertEqual(3, len(bn.premium_ids))
        self.assertEqual(prmToday, latest)

    def test_monthly_premium_no_installments(self):
        """If amount and total are equal only 1 installment"""

        bn = self.create_benefit(self.benefit_create_vals)
        prm = self.create_premium(
            bn, date.today() - relativedelta(days=1), "monthly", 100, 100
        )

        self.assertEqual(1, prm.no_of_installments)
        self.assertEqual(100, prm.amount)
        self.assertEqual(100, prm.total_amount)

    def test_monthly_premium_installments(self):
        """If total is a multiple of amount then installment = total/amount"""

        bn = self.create_benefit(self.benefit_create_vals)
        prm = self.create_premium(
            bn, date.today() - relativedelta(days=1), "monthly", 100, 300
        )

        self.assertEqual(3, prm.no_of_installments)
        self.assertEqual(100, prm.amount)
        self.assertEqual(300, prm.total_amount)

    def test_monthly_premium_installments_plus(self):
        """
        If total is not an even multiple of amount then
        installment = (total/amount) + 1
        """

        bn = self.create_benefit(self.benefit_create_vals)
        prm = self.create_premium(
            bn, date.today() - relativedelta(days=1), "monthly", 100, 350
        )

        self.assertEqual(4, prm.no_of_installments)
        self.assertEqual(100, prm.amount)
        self.assertEqual(350, prm.total_amount)

    def test_reimburse_remaining_no_policy(self):
        """
        If the employee does not have a re-imbursement policy then the
        amount to be re-imbursed is zero.
        """

        bn = self.create_benefit(self.benefit_create_vals)
        earn = self.create_earning(bn, date.today(), "reimburse", 1000)

        self.assertTrue(
            fields.Float.is_zero(
                earn.get_reimburse_remaining(self.eeJohn, date.today()),
                precision_digits=2,
            )
        )

    def test_reimburse_remaining_no_claims(self):
        """
        If no claims have been made in the period the full amount
        remains to be re-imbursed
        """

        bn = self.create_benefit(self.benefit_create_vals)
        self.create_policy(self.eeJohn, bn, date.today())
        earn = self.create_earning(bn, date.today(), "reimburse", 1000)

        self.assertEqual(
            0,
            fields.Float.compare(
                earn.get_reimburse_remaining(self.eeJohn, date.today()),
                1000,
                precision_digits=2,
            ),
        )

    def test_reimburse_remaining_with_claims(self):
        """
        If claims have been made in the period for the full amount then
        nothing remains to be re-imbursed
        """

        bn = self.create_benefit(self.benefit_create_vals)
        earn = self.create_earning(bn, date.today(), "reimburse", 1000)
        pol = self.create_policy(self.eeJohn, bn, date.today())
        clm = self.create_claim(pol, 1000)
        clm.claim_approve()

        self.assertTrue(
            fields.Float.is_zero(
                earn.get_reimburse_remaining(self.eeJohn, date.today()),
                precision_digits=2,
            )
        )

    def test_delete_claim(self):
        """A claim may not be deleted unless it's in a 'draft' state"""

        bn = self.create_benefit(self.benefit_create_vals)
        self.create_earning(bn, date.today(), "reimburse", 1000)
        pol = self.create_policy(self.eeJohn, bn, date.today())
        clm = self.create_claim(pol, 500)
        clm2 = self.create_claim(pol, 500)
        clm2.claim_approve()

        try:
            clm.unlink()
        except UserError:
            self.fail("Unexpected exception")

        with self.assertRaises(UserError):
            clm2.unlink()

    def test_set_draft_from_approve(self):
        """Setting state to 'draft' when it is 'approv' raises an error"""

        bn = self.create_benefit(self.benefit_create_vals)
        pol = self.create_policy(self.eeJohn, bn, date.today())
        clm = self.create_claim(pol, 1000)
        clm.claim_approve()
        with self.assertRaises(UserError):
            clm.set_to_draft()

    def test_multicompany_nosearch(self):
        """A benefit in one company does not appear in searches by another"""

        bn = self.create_benefit(self.benefit_create_vals)
        self.assertNotEqual(
            bn.company_id,
            self.company1,
            "Company of benefit is not equal to 'A Company'",
        )

        lst = (
            self.Benefit.with_user(self.userHRO)
            .with_context(allowed_company_ids=self.company1.ids)
            .search([("code", "=", "A")])
        )
        self.assertEqual(
            len(lst), 0, "Benefit does not appear in searches by 'A Company'"
        )
