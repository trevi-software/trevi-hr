# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields

from . import common


class TestHrPayslip(common.TestHrPayslip):
    def setUp(self):
        super().setUp()

        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.monthly_max_working_days", "30"
        )
        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.working_days_calculation", "defaults"
        )

    def tearDown(self):
        super().tearDown()

        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.monthly_max_working_days", "30"
        )
        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.working_days_calculation", "defaults"
        )

    def test_seniority(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = "result = dictionaries.seniority"

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(
            line[0].amount,
            3.94,
            "The calculated dictionary value 'seniority' is 4 months",
        )

    def test_dictionary_max_hrs(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = "result = dictionaries.max_working_hours"

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            contract_start, start + relativedelta(days=14), self.richard_emp, 5000.0
        )

        # I create a second contract for "Richard"
        self.create_contract(
            start + relativedelta(days=15), False, self.richard_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 2, "I found the Test lines")
        self.assertEqual(
            line[0].amount,
            240.0,
            "The calculated dictionary value 'max_working_hours' is 240",
        )

    def test_dictionary_max_days(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = "result = dictionaries.max_working_days"

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            contract_start, start + relativedelta(days=14), self.richard_emp, 5000.0
        )

        # I create a second contract for "Richard"
        self.create_contract(
            start + relativedelta(days=15), False, self.richard_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 2, "I found the Test lines")
        self.assertEqual(
            line[0].amount,
            30.0,
            "The calculated dictionary value 'max_working_days' is 30",
        )

    def test_dictionary_weekly_hrs(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = "result = dictionaries.max_weekly_hours"

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            contract_start, start + relativedelta(days=14), self.richard_emp, 5000.0
        )

        # I create a second contract for "Richard"
        self.create_contract(
            start + relativedelta(days=15), False, self.richard_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 2, "I found the Test lines")
        self.assertEqual(
            line[0].amount,
            48.0,
            "The calculated dictionary value 'max_weekly_hours' is 48",
        )

    def test_contract_qty(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = "result = dictionaries.CONTRACTS.qty"

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            contract_start, start + relativedelta(days=14), self.richard_emp, 5000.0
        )

        # I create a second contract for "Richard"
        self.create_contract(
            start + relativedelta(days=15), False, self.richard_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 2, "I found the Test lines")
        self.assertEqual(
            line[0].amount, 2.0, "The calculated dictionary value 'CONTRACTS.qty' is 2"
        )

    def test_contract_cummulative_ppf(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = (
            "result = dictionaries.CONTRACTS.cummulative_ppf"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            contract_start, start + relativedelta(days=14), self.richard_emp, 5000.0
        )

        # I create a second contract for "Richard"
        self.create_contract(
            start + relativedelta(days=15), False, self.richard_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 2, "I found the Test lines")
        self.assertEqual(
            line[0].amount,
            1.0,
            "The calculated dictionary value 'CONTRACTS.cumulative_ppf' is 1",
        )

    def test_contract_cummulative_ppf_half(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = (
            "result = dictionaries.CONTRACTS.cummulative_ppf"
        )

        # I create a contract for "Richard"
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            start, start + relativedelta(days=14), self.richard_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(
            line[0].amount,
            0.5,
            "The calculated dictionary value 'CONTRACTS.cumulative_ppf' is 0.5",
        )

    def test_contract_hourly_wage(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = "result = this_contract.hourly_wage"

        # I create a contract for "Richard"
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            start, start + relativedelta(days=14), self.richard_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        res = fields.Float.compare(20.83, line[0].amount, precision_digits=2)
        self.assertEqual(
            res,
            0,
            "The calculated dictionary value 'this_contract.hourly_wage' is 20.83",
        )

    def test_contract_daily_wage(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = "result = this_contract.daily_wage"

        # I create a contract for "Richard"
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            start, start + relativedelta(days=14), self.richard_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(start, end, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        res = fields.Float.compare(166.67, line[0].amount, precision_digits=2)
        self.assertEqual(
            res,
            0,
            "The calculated dictionary value 'this_contract.daily_wage' is 166.67",
        )

    def test_contract_prevps(self):

        # I set the test rule to detect seniority in dictionary
        self.test_rule.amount_python_compute = "result = dictionaries.PREVPS.exists"

        # I set a second test rule that I will use to check previous payslip amount
        self.test_rule = self.Rule.create(
            {
                "name": "Test rule 2",
                "code": "TEST2",
                "category_id": self.ref("payroll.ALW"),
                "sequence": 5,
                "amount_select": "code",
                "amount_python_compute": "result = dictionaries.PREVPS.net",
            }
        )
        self.payroll_structure.write({"rule_ids": [(4, self.test_rule.id)]})

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start1 = date(2022, 3, 1)
        end1 = date(2022, 3, 31)
        start2 = date(2022, 4, 1)
        end2 = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)

        self.apply_contract_cron()

        # I create a Payslip for March, process it and set it to 'done'
        richard_payslip = self.create_payslip(start1, end1, self.richard_emp)
        richard_payslip.compute_sheet()
        richard_payslip.action_payslip_done()

        self.assertEqual(richard_payslip.state, "done", "The first payslip is closed")
        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(line[0].amount, 0.0, "A previous payslip does NOT exist")

        # I create a Payslip for April and process it
        richard_payslip = self.create_payslip(start2, end2, self.richard_emp)
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(line[0].amount, 1.0, "A previous payslip exists")

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST2")
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(
            line[0].amount,
            5000.0,
            "The NET salary for the previous payslip was 5000.00",
        )
