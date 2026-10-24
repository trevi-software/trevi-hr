# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import new_test_user
from odoo.tools.safe_eval import safe_eval

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

    def _policies_for(self, employee):
        """Policies the ``policy_id`` field domain offers to ``employee``.

        The domain is a client-side string; evaluating it with the employee
        chosen in the form is exactly what the web client does.
        """
        domain = self.PremiumPayment._fields["policy_id"].domain
        return self.Policy.search(safe_eval(domain, {"employee_id": employee.id}))

    def test_premium_payment_domain_policy_id(self):
        benefit = self.create_benefit(self.benefit_create_vals)
        self.create_premium(benefit, amount=100.00)
        self.create_policy(self.eePaul, benefit)
        policy = self.create_policy(self.eeJohn, benefit)
        self.PremiumPayment.create(
            {
                "employee_id": self.eeJohn.id,
                "policy_id": policy.id,
                "amount": 100.00,
            }
        )

        # The domain must be a client-side string: a server-side callable is
        # evaluated once on an empty recordset, which yields no policies at all
        # and never refreshes when the employee is changed in the form.
        domain = self.PremiumPayment._fields["policy_id"].domain
        self.assertIsInstance(
            domain,
            str,
            "The policy domain must be a domain string referring to the form's "
            "'employee_id', not a callable evaluated on an empty recordset",
        )
        self.assertIn(
            "employee_id",
            domain,
            "The policy domain must be filtered on the selected employee",
        )

        domain_list = self._policies_for(self.eeJohn)
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

        # The same domain must follow the employee selected in the form.
        domain_list = self._policies_for(self.eePaul)
        self.assertEqual(
            len(domain_list),
            1,
            "Only the policy for 'Paul' should be in the list of policies",
        )
        self.assertEqual(domain_list.employee_id, self.eePaul)

    def test_premium_payment_domain_excludes_benefits_without_premium(self):
        """Benefits that have no premium are not offered for a payment."""
        with_premium = self.create_benefit(self.benefit_create_vals)
        self.create_premium(with_premium, amount=100.00)
        without_premium = self.create_benefit(
            dict(self.benefit_create_vals, name="No premium benefit", code="NOPRM")
        )
        self.assertFalse(without_premium.has_premium)
        with_policy = self.create_policy(self.eeJohn, with_premium)
        self.create_policy(self.eeJohn, without_premium)

        domain_list = self._policies_for(self.eeJohn)
        self.assertEqual(
            domain_list,
            with_policy,
            "Only policies of benefits that have premiums may be selected",
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
