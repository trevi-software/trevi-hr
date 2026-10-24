# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import new_test_user

from odoo.addons.hr_benefit.tests import common as benefit_common


class TestBenefit(benefit_common.TestBenefitCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.PremiumPayment = cls.env["hr.benefit.premium.payment"]
        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="pm",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
        )
        # Payroll user
        cls.userPU = new_test_user(
            cls.env,
            login="pu",
            groups="base.group_user,payroll.group_payroll_user",
            name="Payroll manager",
        )

    def test_premium_payment_initial_state(self):
        benefit = self.create_benefit(self.benefit_create_vals)
        policy = self.create_policy(self.eeJohn, benefit)
        pp = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": policy.id,
                "amount": 100.00,
            }
        )
        self.assertEqual(pp.state, "draft", "Initial state must be 'draft'")

    def test_premium_payment_date_default_is_dynamic(self):
        """The date default must be evaluated per record, not at import."""
        # Odoo 19 keeps the field arguments in ``_args__``; the default must be
        # the callable, not the date string it returned when the model loaded.
        default = self.PremiumPayment._fields["date"]._args__["default"]
        self.assertTrue(
            callable(default),
            "The payment date default must be a callable that is evaluated for "
            "each new payment, not a date frozen when the model is loaded",
        )
        self.assertIs(default, fields.Date.today)

    def test_premium_payment_domain_policy_id(self):
        benefit = self.create_benefit(self.benefit_create_vals)
        self.create_premium(benefit, amount=100.00)
        self.create_policy(self.eePaul, benefit)
        policy = self.create_policy(self.eeJohn, benefit)
        pp = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": policy.id,
                "amount": 100.00,
            }
        )

        # ``Many2one.get_domain_list`` does not exist anymore in 19.0. The
        # ``policy_id`` domain is produced by ``_compute_policy_id_domain``,
        # which is what the field's domain callable invokes for this record.
        domain = pp._compute_policy_id_domain()
        domain_list = self.Policy.search(domain)
        self.assertEqual(
            len(domain_list),
            1,
            "Only the policy for 'John' should be in the list of policies",
        )
        self.assertIn(
            policy,
            domain_list,
            "The policy for 'John' should be in the list of policies",
        )

    def test_premium_payment_unlink(self):
        benefit = self.create_benefit(self.benefit_create_vals)
        benefit.multi_policy = True
        self.create_premium(benefit, amount=100.00)
        polDraft = self.create_policy(self.eeJohn, benefit)
        polPending = self.create_policy(self.eeJohn, benefit)
        polCancel = self.create_policy(self.eeJohn, benefit)
        polDone = self.create_policy(self.eeJohn, benefit)
        ppDraft = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": polDraft.id,
                "amount": 100.00,
            }
        )
        ppPending = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": polPending.id,
                "amount": 100.00,
            }
        )
        ppPending.action_pending()
        ppCancel = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": polCancel.id,
                "amount": 100.00,
            }
        )
        ppCancel.action_cancel()
        ppDone = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": polDone.id,
                "amount": 100.00,
            }
        )
        ppDone.action_done()

        self.assertEqual(ppDraft.state, "draft")
        try:
            ppDraft.unlink()
        except UserError:
            self.fail("Unexpected UserError exception!")

        self.assertEqual(ppPending.state, "pending")
        with self.assertRaises(UserError):
            ppPending.unlink()

        self.assertEqual(ppCancel.state, "cancel")
        with self.assertRaises(UserError):
            ppCancel.unlink()

        self.assertEqual(ppDone.state, "done")
        with self.assertRaises(UserError):
            ppDone.unlink()

    def test_premium_payment_unlink_force_delete(self):
        benefit = self.create_benefit(self.benefit_create_vals)
        benefit.multi_policy = True
        self.create_premium(benefit, amount=100.00)
        polPending = self.create_policy(self.eeJohn, benefit)
        polCancel = self.create_policy(self.eeJohn, benefit)
        polDone = self.create_policy(self.eeJohn, benefit)
        ppPending = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": polPending.id,
                "amount": 100.00,
            }
        )
        ppPending.action_pending()
        ppCancel = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": polCancel.id,
                "amount": 100.00,
            }
        )
        ppCancel.action_cancel()
        ppDone = self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": polDone.id,
                "amount": 100.00,
            }
        )
        ppDone.action_done()

        self.assertEqual(ppPending.state, "pending")
        try:
            ppPending.with_context(force_delete=True).unlink()
        except UserError:
            self.fail("Unexpected UserError exception!")

        self.assertEqual(ppCancel.state, "cancel")
        try:
            ppCancel.with_context(force_delete=True).unlink()
        except UserError:
            self.fail("Unexpected UserError exception!")

        self.assertEqual(ppDone.state, "done")
        try:
            ppDone.with_context(force_delete=True).unlink()
        except UserError:
            self.fail("Unexpected UserError exception!")
