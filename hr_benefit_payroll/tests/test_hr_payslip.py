# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo import fields
from odoo.tests import Form

from odoo.addons.hr_benefit.tests import common as benefit_common


class TestBenefit(benefit_common.TestBenefitCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Payslip = cls.env["hr.payslip"]
        cls.PayrollStructure = cls.env["hr.payroll.structure"]
        cls.SalaryRule = cls.env["hr.salary.rule"]
        cls.SalaryRuleCateg = cls.env["hr.salary.rule.category"]

        cls.categ_basic = cls.SalaryRuleCateg.create(
            {
                "name": "Basic",
                "code": "BASIC",
            }
        )

        cls.rule_basic = cls.SalaryRule.create(
            {
                "name": "Basic Salary",
                "code": "BASIC",
                "sequence": 1,
                "category_id": cls.categ_basic.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": "result = contract.wage",
            }
        )

        cls.categ_deduction = cls.SalaryRuleCateg.create(
            {
                "name": "Deduction",
                "code": "DED",
            }
        )

        cls.payroll_structure = cls.PayrollStructure.create(
            {
                "name": "Salary Structure for Sales Person",
                "code": "SP",
                "company_id": cls.env.ref("base.main_company").id,
                "rule_ids": [
                    (4, cls.rule_basic.id),
                ],
            }
        )

    def _create_premium_structure(self, benefit):
        """Structure whose premium rule deducts ``hr_benefit.<CODE>``.

        ``has_premium_payment`` marks the rule as the one that actually books
        the benefit premium deduction on the payslip.
        """
        rule_premium = self.SalaryRule.create(
            {
                "name": "Benefit Premium",
                "code": "BENPRM",
                "sequence": 10,
                "category_id": self.categ_deduction.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": (
                    f"result = hr_benefit.{benefit.code}.deductions"
                ),
                "has_premium_payment": True,
                "benefit_id": benefit.id,
            }
        )
        return self.PayrollStructure.create(
            {
                "name": "Salary Structure with Benefit Premium",
                "code": "SPP",
                "company_id": self.env.ref("base.main_company").id,
                "rule_ids": [
                    (4, self.rule_basic.id),
                    (4, rule_premium.id),
                ],
            }
        )

    def create_contract(self, eid, start, end=None, trial_end=None, struct=None):
        """Create the ``hr.version`` that represents a contract in 19.0.

        ``hr.contract`` was merged into ``hr``: a contract is now an
        ``hr.version`` with ``contract_date_start``/``contract_date_end``.
        The version must be dated on its own start date because ``date_start``
        is ``max(date_version, contract_date_start)``; leaving ``date_version``
        at today would exclude the backdated period from the contract.
        """
        return self.env["hr.version"].create(
            {
                "name": "Contract",
                "employee_id": eid,
                "date_version": start,
                "contract_date_start": start,
                "contract_date_end": end,
                "wage": 1,
                "trial_date_end": trial_end,
                "struct_id": (struct or self.payroll_structure).id,
            }
        )

    def test_get_benefit_policies_for_payslip_premium(self):
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        bvals = self.benefit_create_vals.copy()
        bvals.update({"link2payroll": True})
        benefit = self.create_benefit(bvals)
        self.create_premium(benefit, start=start, amount=100.00)
        self.create_policy(self.eeJohn, benefit, start)
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()

        self.assertEqual(
            len(slip.benefit_line_ids),
            1,
            "There should be only 1 benefit line attached to payslip",
        )
        self.assertEqual(
            slip.benefit_line_ids[0].earnings, 0, "Benefit line should show no earnings"
        )
        self.assertEqual(
            slip.benefit_line_ids[0].deductions,
            100,
            "Benefit line should show a deduction of benefit premium amount",
        )

    def test_get_benefit_policies_for_payslip_premium_override(self):
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        bvals = self.benefit_create_vals.copy()
        bvals.update({"link2payroll": True})
        benefit = self.create_benefit(bvals)
        self.create_premium(benefit, start=start, amount=100.00)
        self.create_policy(self.eeJohn, benefit, start, premium=200.00)
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()

        self.assertEqual(
            len(slip.benefit_line_ids),
            1,
            "There should be only 1 benefit line attached to payslip",
        )
        self.assertEqual(
            slip.benefit_line_ids[0].earnings, 0, "Benefit line should show no earnings"
        )
        self.assertEqual(
            slip.benefit_line_ids[0].deductions,
            200,
            "Benefit line should show a deduction of the override amount",
        )

    def test_get_benefit_policies_for_payslip_premium_total(self):
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        bvals = self.benefit_create_vals.copy()
        bvals.update({"link2payroll": True})
        benefit = self.create_benefit(bvals)
        self.create_premium(benefit, start=start, amount=100.00, total=500.00)
        self.create_policy(self.eeJohn, benefit, start)
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()

        self.assertEqual(
            len(slip.benefit_line_ids),
            1,
            "There should be only 1 benefit line attached to payslip",
        )
        self.assertEqual(
            slip.benefit_line_ids[0].earnings, 0, "Benefit line should show no earnings"
        )
        self.assertEqual(
            slip.benefit_line_ids[0].deductions,
            100,
            "Benefit line should show a deduction of benefit premium amount",
        )

    def test_get_benefit_policies_for_payslip_allowance(self):
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        bvals = self.benefit_create_vals.copy()
        bvals.update({"link2payroll": True})
        benefit = self.create_benefit(bvals)
        self.create_earning(benefit, start=start, allowance=500.00)
        self.create_policy(self.eeJohn, benefit, start)
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()

        self.assertEqual(
            len(slip.benefit_line_ids),
            1,
            "There should be only 1 benefit line attached to payslip",
        )
        self.assertEqual(
            slip.benefit_line_ids[0].earnings,
            500,
            "Benefit line should show 500.00 earnings",
        )
        self.assertEqual(
            slip.benefit_line_ids[0].deductions,
            0,
            "Benefit line should show NO deductions",
        )

    def test_get_benefit_policy_partial(self):
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        policy_end = date(2021, 1, 15)
        self.benefit_create_vals.update({"link2payroll": True})
        benefit = self.create_benefit(self.benefit_create_vals)
        self.create_premium(benefit, start=start, amount=100.00)
        self.create_policy(self.eeJohn, benefit, start, policy_end)
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()

        self.assertEqual(
            fields.Float.compare(slip.benefit_line_ids[0].ppf, 0.5, precision_digits=1),
            0,
            "The benefit ppf should be 0.5 because the policy lasted 1/2 month",
        )

    def test_get_benefit_policy_allowance(self):
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        self.benefit_create_vals.update({"link2payroll": True})
        benefit = self.create_benefit(self.benefit_create_vals)
        self.create_earning(benefit, start=start, allowance=100.00)
        self.create_policy(self.eeJohn, benefit, start)
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()

        self.assertEqual(
            len(slip.benefit_line_ids),
            1,
            "There should be only 1 benefit line attached to payslip",
        )
        self.assertEqual(
            slip.benefit_line_ids[0].earnings,
            100,
            "Benefit should indicate allowance of 100",
        )
        self.assertEqual(
            slip.benefit_line_ids[0].deductions,
            0,
            "Benefit line should show no dedections",
        )

    def test_benefit_policy_ppf(self):
        """
        Test for off-by-one error when calculating policy and payroll days.
        29 / 30 as opposed to 30 / 31. Manifests as ppf calculation error.
        """

        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        self.benefit_create_vals.update({"link2payroll": True})
        benefit = self.create_benefit(self.benefit_create_vals)
        self.create_earning(benefit, start=start, allowance=100.00)
        self.create_policy(self.eeJohn, benefit, start + timedelta(days=1))
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()

        self.assertEqual(
            len(slip.benefit_line_ids),
            1,
            "There should be only 1 benefit line attached to payslip",
        )
        self.assertEqual(
            round(slip.benefit_line_ids[0].ppf, 4),
            0.9677,
            "Benefit should indicate PPF of 0.9677",
        )
        self.assertEqual(
            benefit.code,
            slip.benefit_line_ids[0].code,
            "The benefit appears in the payslip's benefit lines",
        )

    def test_onchange_deletes_old_values(self):
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        self.benefit_create_vals.update({"link2payroll": True})
        benefit = self.create_benefit(self.benefit_create_vals)
        self.create_earning(benefit, start=start, allowance=100.00)
        self.create_policy(self.eeJohn, benefit, start)
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()
        slip.onchange_employee()

        self.assertEqual(
            len(slip.benefit_line_ids),
            1,
            "There should be only 1 benefit line attached to payslip",
        )

    def test_no_employee_no_contract(self):
        frm = Form(self.Payslip)
        frm.date_from = date(2021, 1, 1)
        self.assertTrue(
            True, "If we've reached this far without an exception thrown we're good"
        )

    def test_benefit_policy_premium_refund(self):
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        self.benefit_create_vals.update({"link2payroll": True})
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(
            bn,
            start,
            ptype="monthly",
            amount=100,
            total=300,
        )
        pol = self.create_policy(self.eeJohn, bn, start)
        pol.state_open()
        # A premium payment is only booked for a premium that was actually
        # deducted, so the contract needs the premium salary rule.
        struct = self._create_premium_structure(bn)
        self.create_contract(self.eeJohn.id, start, struct=struct)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()
        self.assertEqual(
            bn.code,
            slip.benefit_line_ids[0].code,
            "The benefit appears in the payslip's benefit lines",
        )
        slip.compute_sheet()
        slip.action_payslip_done()
        self.assertEqual(
            len(slip.premium_payment_ids), 1, "There is one premium payment"
        )
        self.assertEqual(
            slip.premium_payment_ids[0].state,
            "done",
            "The premium payment is done",
        )

        slip.refund_sheet()

        self.assertEqual(
            slip.premium_payment_ids[0].state,
            "cancel",
            "The premium payment has been cancelled",
        )

    def _prepare_premium_slip(self, benefit, start=None):
        start = start or date(2021, 1, 1)
        end = date(2021, 1, 31)
        policy = self.create_policy(self.eeJohn, benefit, start)
        policy.state_open()
        struct = self._create_premium_structure(benefit)
        self.create_contract(self.eeJohn.id, start, struct=struct)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()
        return slip, policy

    def test_no_premium_payment_without_deduction(self):
        """A policy whose premium no rule deducted must not be marked as paid."""
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        self.benefit_create_vals.update({"link2payroll": True})
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(bn, start, ptype="monthly", amount=100, total=300)
        pol = self.create_policy(self.eeJohn, bn, start)
        pol.state_open()
        # Contract uses the plain structure: no rule deducts the premium.
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()
        slip.compute_sheet()
        slip.action_payslip_done()

        self.assertFalse(
            slip.premium_payment_ids,
            "No premium payment may be recorded when no rule deducted it",
        )
        self.assertEqual(
            pol._get_paid_amount(),
            0,
            "An undeducted premium must not count towards the paid amount",
        )

    def test_premium_payment_amount_matches_deduction(self):
        """The payment is the per-period premium, not the annual amount."""
        start = date(2021, 1, 1)
        self.benefit_create_vals.update({"link2payroll": True})
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(bn, start, ptype="annual", amount=1200)
        slip, _policy = self._prepare_premium_slip(bn)
        slip.compute_sheet()
        slip.action_payslip_done()

        self.assertEqual(
            len(slip.premium_payment_ids),
            1,
            "There should be one premium payment",
        )
        self.assertEqual(
            slip.premium_payment_ids.amount,
            100,
            "The annual premium must be split over the 12 pay periods",
        )

    def test_premium_payment_recorded_per_policy(self):
        """Each policy of a multi-policy benefit gets its own payment."""
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        self.benefit_create_vals.update({"link2payroll": True})
        bn = self.create_benefit(self.benefit_create_vals)
        bn.multi_policy = True
        self.create_premium(bn, start, ptype="monthly", amount=100)
        struct = self._create_premium_structure(bn)
        self.create_contract(self.eeJohn.id, start, struct=struct)
        pol_a = self.create_policy(self.eeJohn, bn, start)
        pol_a.name = "Policy A"
        pol_b = self.create_policy(self.eeJohn, bn, start)
        pol_b.name = "Policy B"
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()
        slip.compute_sheet()
        slip.action_payslip_done()

        payments = slip.premium_payment_ids
        self.assertEqual(len(payments), 2, "One payment per policy")
        self.assertEqual(
            set(payments.mapped("policy_id").ids),
            {pol_a.id, pol_b.id},
            "Every payment must be booked on its own policy",
        )
        self.assertEqual(sum(payments.mapped("amount")), 200)

    def test_one_day_policy_still_counts(self):
        """A policy ending on the first day of the period contributes."""
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        policy_start = date(2020, 12, 1)
        self.benefit_create_vals.update({"link2payroll": True})
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_premium(bn, policy_start, ptype="monthly", amount=100)
        self.create_policy(self.eeJohn, bn, policy_start, start)
        self.create_contract(self.eeJohn.id, start)
        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
            }
        )
        slip.onchange_employee()

        line = slip.benefit_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(
            line.deductions,
            100,
            "The premium of the overlapping day must be deducted",
        )
        self.assertGreater(
            line.ppf,
            0,
            "A one-day overlap must have a non-zero payroll period factor",
        )

    def test_get_payslip_vals_returns_one2many_commands(self):
        """get_payslip_vals must return values a payslip can be created with."""
        start = date(2021, 1, 1)
        end = date(2021, 1, 31)
        self.benefit_create_vals.update({"link2payroll": True})
        bn = self.create_benefit(self.benefit_create_vals)
        self.create_earning(bn, start=start, allowance=100.00)
        self.create_policy(self.eeJohn, bn, start)
        self.create_contract(self.eeJohn.id, start)

        vals = self.Payslip.get_payslip_vals(start, end, employee_id=self.eeJohn.id)[
            "value"
        ]
        commands = vals["benefit_line_ids"]
        self.assertTrue(
            all(
                isinstance(command, tuple) and command[0] in (0, 2)
                for command in commands
            ),
            "benefit_line_ids must be a list of One2many commands",
        )

        slip = self.Payslip.create(
            {
                "employee_id": self.eeJohn.id,
                "date_from": start,
                "date_to": end,
                "contract_id": vals["contract_id"],
                "struct_id": vals["struct_id"],
                "benefit_line_ids": commands,
            }
        )
        self.assertEqual(
            len(slip.benefit_line_ids),
            1,
            "Applying the returned commands must create the benefit line",
        )
        self.assertEqual(slip.benefit_line_ids.earnings, 100)
