# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from . import test_common


class TestHrPayslip(test_common.TestHrPayslip):
    def setUp(self):
        super().setUp()

        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.daily_max_regular_hours", "8"
        )
        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.weekly_max_regular_hours", "48"
        )
        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.monthly_max_working_days", "30"
        )
        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.working_days_calculation", "defaults"
        )

    def tearDown(self):
        super().tearDown()

        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.daily_max_regular_hours", "8"
        )
        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.weekly_max_regular_hours", "48"
        )
        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.monthly_max_working_days", "30"
        )
        self.env["ir.config_parameter"].set_param(
            "payroll_payslip_dictionary.working_days_calculation", "defaults"
        )

    def test_contract_ppf_no_end_date(self):

        # I create a contract for "Richard"
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            start - relativedelta(years=1), False, self.alice_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        alice_payslip = self.create_payslip(start, end, self.alice_emp)
        alice_payslip.compute_sheet()

        line = alice_payslip.line_ids.filtered(lambda l: l.code == "BASIC")
        self.assertTrue(len(line) == 1, "I found the BASIC salary line")
        self.assertEqual(
            line[0].amount,
            5000.00,
            "The calculated amount is EQUAL to the employee's monthly wage",
        )

    def test_contract_ppf_exact_end_date(self):

        # I create a contract for "Richard"
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(start, end, self.alice_emp, 5000.0)

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        alice_payslip = self.create_payslip(start, end, self.alice_emp)
        alice_payslip.compute_sheet()

        line = alice_payslip.line_ids.filtered(lambda l: l.code == "BASIC")
        self.assertTrue(len(line) == 1, "I found the BASIC salary line")
        self.assertEqual(
            line[0].amount,
            5000.00,
            "The calculated amount is EQUAL to the employee's salary",
        )

    def test_contract_ppf_half(self):

        # I create a contract for "Richard"
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            start, start + relativedelta(days=14), self.alice_emp, 5000.0
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        alice_payslip = self.create_payslip(start, end, self.alice_emp)
        alice_payslip.compute_sheet()

        line = alice_payslip.line_ids.filtered(lambda l: l.code == "BASIC")
        self.assertTrue(len(line) == 1, "I found the BASIC salary line")
        self.assertEqual(
            line[0].amount,
            2500.00,
            "The calculated amount is half the employee's monthly wage",
        )

    def test_contract_ppf_2contracts(self):

        # I create a contract for "Richard"
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(
            start, start + relativedelta(days=14), self.alice_emp, 5000.0
        )

        # I create a second contract for "Richard"
        start2 = date(2022, 4, 16)
        self.create_contract(
            start2,
            start2 + relativedelta(days=14),
            self.alice_emp,
            10000.0,
            "2nd Contract for Richard",
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        alice_payslip = self.create_payslip(start, end, self.alice_emp)
        alice_payslip.compute_sheet()

        lines = alice_payslip.line_ids.filtered(lambda l: l.code == "BASIC")
        self.assertTrue(len(lines) == 2, "I found the BASIC salary lines")

        sum_amounts = sum([line.amount for line in lines])
        self.assertEqual(
            sum_amounts,
            7500.00,
            "The calculated amount is half of first wage + half of second wage",
        )

    def test_contract_ppf_days_less_than_default_days(self):

        # I create a contract for "Richard" of 10 days
        pay_start = date(2022, 4, 1)
        pay_end = date(2022, 4, 30)
        c1_start = date(2022, 3, 30)
        c1_end = date(2022, 4, 10)
        self.create_contract(c1_start, c1_end, self.alice_emp, 5000.0)

        # I create a second contract for "Richard" of another 10 days
        c2_start = date(2022, 4, 11)
        c2_end = date(2022, 4, 20)
        self.create_contract(
            c2_start, c2_end, self.alice_emp, 15000.0, "2nd Contract for Richard"
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        alice_payslip = self.create_payslip(pay_start, pay_end, self.alice_emp)
        alice_payslip.compute_sheet()

        lines = alice_payslip.line_ids.filtered(lambda l: l.code == "BASIC")
        self.assertTrue(len(lines) == 2, "I found the BASIC salary lines")

        sum_amounts = sum([line.amount for line in lines])
        self.assertEqual(
            sum_amounts,
            6666.00,
            "The calculated amount is 0.3333 first wage + 0.3333 of second wage",
        )

    def test_contract_ppf_february(self):

        # I create a contract for "Richard"
        start = date(2022, 2, 1)
        end = date(2022, 2, 15)
        month_end = date(2022, 2, 28)
        self.create_contract(start, end, self.alice_emp, 5000.0)

        # I create a second contract for "Richard"
        start2 = date(2022, 2, 16)
        self.create_contract(
            start2, month_end, self.alice_emp, 10000.0, "2nd Contract for Richard"
        )

        self.apply_contract_cron()

        # I create an employee Payslip and process it
        alice_payslip = self.create_payslip(start, month_end, self.alice_emp)
        alice_payslip.compute_sheet()

        lines = alice_payslip.line_ids.filtered(lambda l: l.code == "BASIC")
        self.assertTrue(len(lines) == 2, "I found the BASIC salary lines")

        sum_amounts = sum([line.amount for line in lines])
        self.assertEqual(
            sum_amounts,
            7333.50,
            "The calculated amount is 0.5333 x first wage + 0.4667 * second wage",
        )
