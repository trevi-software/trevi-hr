# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError

from . import common


class TestBenefit(common.TestBenefitCommon):
    def test_policy_onchange_benefit(self):
        """When the benefit changes so should the code, premium and earnings amounts"""

        bn1 = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn1, date.today() - relativedelta(days=1), "monthly", 100, 100
        )
        bn2 = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn2, date.today(), allowance=1000)
        pol = self.create_policy(self.eeJohn, bn1, date.today())
        self.assertEqual(bn1, pol.benefit_id)
        self.assertEqual(bn1.code, pol.benefit_code)
        self.assertEqual("draft", pol.state)
        self.assertTrue(fields.Float.is_zero(pol.advantage_amount, precision_digits=2))
        self.assertEqual(100, pol.premium_amount)
        self.assertEqual(100, pol.premium_total)

        pol.benefit_id = bn2.id

        self.assertEqual(bn2, pol.benefit_id)
        self.assertEqual(bn2.code, pol.benefit_code)
        self.assertEqual("draft", pol.state)
        self.assertEqual(
            0, fields.Float.compare(1000, pol.advantage_amount, precision_digits=2)
        )
        self.assertTrue(fields.Float.is_zero(pol.premium_amount, precision_digits=2))
        self.assertTrue(fields.Float.is_zero(pol.premium_total, precision_digits=2))

    def test_policy_premium_latest(self):
        """
        If there are multiple premiums get the lastest one as of today, even if
        it was after the policy creation date.
        """

        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn,
            date.today() - relativedelta(days=60),
            ptype="monthly",
            amount=100,
        )
        self.create_premium(
            bn,
            date.today() - relativedelta(days=30),
            ptype="monthly",
            amount=200,
        )
        pol = self.create_policy(self.eeJohn, bn, date.today() - relativedelta(days=45))

        self.assertEqual(200, pol.premium_amount)

    def test_policy_premium_installments(self):
        """If total is a multiple of amount then installment = total/amount"""

        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn,
            date.today() - relativedelta(days=1),
            ptype="monthly",
            amount=100,
            total=300,
        )
        pol = self.create_policy(self.eeJohn, bn, date.today())

        self.assertEqual(100, pol.premium_amount)
        self.assertEqual(300, pol.premium_total)
        self.assertEqual(3, pol.premium_installments)

    def test_monthly_premium_installments_plus(self):
        """
        If total is not an even multiple of amount then
        installment = (total/amount) + 1
        """

        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn, date.today() - relativedelta(days=1), "monthly", 100, 350
        )
        pol = self.create_policy(self.eeJohn, bn, date.today())

        self.assertEqual(100, pol.premium_amount)
        self.assertEqual(350, pol.premium_total)
        self.assertEqual(4, pol.premium_installments)

    def test_min_employed_days(self):
        """
        If the employee has been employed less than the min. days specified in
        the benefit a UserError exception is raised
        """

        cc = self.create_contract(
            "draft", "done", date.today() - relativedelta(days=10)
        )
        cc.signal_confirm()
        bn = self.create_benefit({"name": "B", "code": "B", "min_employed_days": 30})
        self.create_earning(bn, date.today(), allowance=1000)

        with self.assertRaises(UserError):
            self.create_policy(self.eeJohn, bn, date.today())

    def test_no_multipolicy(self):
        """
        If the benefit hasn't enabled concurrent policies an attempt to enroll an
        employee more than once will cause a UserError exception to be raised
        """

        bnNoMulti = self.create_benefit({"name": "B", "code": "B"})
        bnMulti = self.create_benefit({"name": "C", "code": "C", "multi_policy": True})
        self.create_earning(bnNoMulti, date.today(), allowance=1000)
        self.create_earning(bnMulti, date.today(), allowance=3000)
        self.create_policy(self.eeJohn, bnNoMulti, date.today())
        self.create_policy(self.eeJohn, bnMulti, date.today())

        with self.assertRaises(UserError):
            self.create_policy(self.eeJohn, bnNoMulti, date.today())

        try:
            self.create_policy(self.eeJohn, bnMulti, date.today())
        except UserError:
            self.fail("An unexpected exception was raised")

    def test_policy_unlink(self):
        """Deleting a policy not in 'Draft' state raises a UserError"""

        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today(), allowance=1000)
        pol = self.create_policy(self.eeJohn, bn, date.today())
        pol.state_open()

        with self.assertRaises(UserError):
            pol.unlink()

    def test_set_draft_from_open(self):
        """Setting state to 'Draft' when it is 'open' raises an error"""

        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today(), allowance=1000)
        pol = self.create_policy(self.eeJohn, bn, date.today())
        pol.state_open()

        with self.assertRaises(UserError):
            pol.state = "draft"

    def test_set_done_from_draft(self):
        """Setting state to 'Done' when it isn't 'open' raises an error"""

        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today(), allowance=1000)
        pol = self.create_policy(self.eeJohn, bn, date.today())

        with self.assertRaises(UserError):
            pol.state_done()

    def test_change_from_done(self):
        """Setting state to any value when it is 'done' raises an error"""

        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today(), allowance=1000)
        pol = self.create_policy(self.eeJohn, bn, date.today())
        pol.state_open()
        pol.state_done()

        with self.assertRaises(UserError):
            pol.state = "draft"
        with self.assertRaises(UserError):
            pol.state = "open"

    def test_override_earning(self):
        """User can override the calculated earning amount"""

        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today(), allowance=1000)
        pol = self.create_policy(self.eeJohn, bn, date.today(), advantage=4400)
        pol.state_open()

        self.assertEqual(4400, pol.advantage_amount)

    def test_end_policy_wizard(self):
        """Calling end_policy() method of wizard sets end date and state = 'done'"""

        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today(), allowance=1000)
        pol = self.create_policy(self.eeJohn, bn, date.today())
        pol.state_open()
        self.assertFalse(pol.end_date)
        self.assertEqual("open", pol.state)

        wiz = self.EndWizard.with_context({"end_benefit_policy_id": pol.id}).create({})
        wiz.date = date.today()
        wiz.end_policy()

        self.assertEqual(date.today(), pol.end_date)
        self.assertEqual(pol.state, "done")

    def test_endroll_single_employee(self):
        """Running the enroll employee wizard creates a policy for the employee"""

        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today(), allowance=1000)

        wiz = self.EnrollWizard.with_context({"active_id": bn.id}).create(
            {"employee_id": self.eeJohn.id, "start_date": date.today()}
        )
        wiz.do_enroll()

        policy_ids = self.Policy.search([("employee_id", "=", self.eeJohn.id)])
        self.assertEqual(1, len(policy_ids))
        self.assertEqual(bn, policy_ids[0].benefit_id)
        self.assertEqual(date.today(), policy_ids[0].start_date)
        self.assertFalse(policy_ids[0].end_date)

    def test_endroll_multi_employee(self):
        """
        Running the enroll multiple employees wizard creates a policy for
        multiple employees
        """

        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today(), allowance=1000)

        wiz = self.EnrollMultiWizard.with_context({"active_id": bn.id}).create(
            {"employee_ids": [(6, 0, [self.eeJohn.id])], "start_date": date.today()}
        )
        wiz.do_multi_enroll()

        policy_ids = self.Policy.search([("employee_id", "=", self.eeJohn.id)])
        self.assertEqual(1, len(policy_ids))
        self.assertEqual(bn, policy_ids[0].benefit_id)
        self.assertEqual(date.today(), policy_ids[0].start_date)
        self.assertFalse(policy_ids[0].end_date)
