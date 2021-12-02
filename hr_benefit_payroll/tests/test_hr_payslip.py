# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo import fields

from odoo.addons.hr_benefit.tests import common as benefit_common


class TestBenefit(benefit_common.TestBenefitCommon):
    @classmethod
    def setUpClass(cls):
        super(TestBenefit, cls).setUpClass()

        cls.Payslip = cls.env["hr.payslip"]

    def create_contract(
        self, eid, state, kanban_state, start, end=None, trial_end=None, pps_id=None
    ):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": eid,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
                "struct_id": self.env.ref("payroll.structure_base").id,
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
        self.create_contract(self.eeJohn.id, "draft", "done", start).signal_confirm()
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
        self.create_contract(self.eeJohn.id, "draft", "done", start).signal_confirm()
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
        self.create_contract(self.eeJohn.id, "draft", "done", start).signal_confirm()
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
        self.create_contract(self.eeJohn.id, "draft", "done", start).signal_confirm()
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
        self.create_contract(self.eeJohn.id, "draft", "done", start).signal_confirm()
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
        self.create_contract(self.eeJohn.id, "draft", "done", start).signal_confirm()
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
