# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from . import common


class TestPresencePolicy(common.TestHrPayslip):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.OtPolicy = cls.env["hr.policy.ot"]
        cls.OtPolicyLine = cls.env["hr.policy.line.ot"]

        # Create a salary rule for OT tests and add it to the salary structure
        cls.ot_test_rule = cls.Rule.create(
            {
                "name": "OT Test rule",
                "code": "OTTEST",
                "category_id": cls.env.ref("payroll.ALW").id,
                "sequence": 6,
                "amount_select": "code",
                "amount_python_compute": "result = 0",
            }
        )
        cls.payroll_structure.write({"rule_ids": [(4, cls.ot_test_rule.id)]})

        # Create a salary rule for a second OT tests, add it to salary structure
        cls.ot_test_rule2 = cls.Rule.create(
            {
                "name": "OT 2 Test rule",
                "code": "OTTEST2",
                "category_id": cls.env.ref("payroll.ALW").id,
                "sequence": 7,
                "amount_select": "code",
                "amount_python_compute": "result = 0",
            }
        )
        cls.payroll_structure.write({"rule_ids": [(4, cls.ot_test_rule2.id)]})

        # Create a OT Policy
        cls.ot_policy = cls.OtPolicy.create(
            {"name": "POLICY OT", "date": date(2000, 1, 1)}
        )
        cls.OtPolicyLine.create(
            {
                "name": "OT Line - Normal workday",
                "code": "OTD",
                "type": "daily",
                "active_after": 8.0 * 60,
                "rate": 1.5,
                "policy_id": cls.ot_policy.id,
                "tz": "Africa/Addis_Ababa",
            }
        )
        cls.OtPolicyLine.create(
            {
                "name": "Night OT Line",
                "code": "OTN",
                "type": "daily",
                "active_after": 0.0,
                "active_start_time": "22:00",
                "active_end_time": "06:00",
                "rate": 1.75,
                "policy_id": cls.ot_policy.id,
                "tz": "Africa/Addis_Ababa",
            }
        )
        cls.OtPolicyLine.create(
            {
                "name": "OT Line - Rest Day",
                "code": "OTR",
                "type": "restday",
                "active_after": 8.0 * 60,
                "rate": 4.0,
                "policy_id": cls.ot_policy.id,
                "tz": "Africa/Addis_Ababa",
            }
        )
        cls.OtPolicyLine.create(
            {
                "name": "OT Line - Holiday",
                "code": "OTH",
                "type": "holiday",
                "active_after": 8.0 * 60,
                "rate": 2.5,
                "policy_id": cls.ot_policy.id,
                "tz": "Africa/Addis_Ababa",
            }
        )

        # I put the presence policy in the policy group
        cls.default_policy_group.ot_policy_ids = [(4, cls.ot_policy.id)]

        # Create a public holiday
        cls.public_holiday = cls.PublicHoliday.create(
            {
                "year": 2022,
                "line_ids": [
                    (0, 0, {"name": "Foo", "date": date(2022, 4, 2)}),
                ],
            }
        )

    def test_daily_ot(self):

        # I set the test rules to detect the number of regular and OT worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )
        self.ot_test_rule.amount_python_compute = (
            "result_rate = worked_days.OTD.rate * 100 \n"
            "result = worked_days.OTD.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for one day
        self.Attendance.create(
            {
                "employee_id": self.richard_emp.id,
                "check_in": self.localize_dt(
                    datetime.combine(start, datetime.strptime("08:00", "%H:%M").time()),
                    self.richard_emp.tz,
                    reverse=True,
                ),
                "check_out": self.localize_dt(
                    datetime.combine(start, datetime.strptime("17:30", "%H:%M").time()),
                    self.richard_emp.tz,
                    reverse=True,
                ),
            }
        )

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(
            start, end, self.richard_emp, user=self.payroll_user
        )
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Normal Test line")
        self.assertEqual(
            line[0].amount,
            8.0,
            "The number of regularly worked hours is 8",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Regular hours are paid at the normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST")
        self.assertEqual(len(line), 1, "I found the OT Test line")
        self.assertEqual(
            line[0].amount,
            1.5,
            "The number of daily OT worked hours is 1:30",
        )
        self.assertEqual(
            line[0].rate,
            150,
            "Daily OT hours are paid at 1.5x normal rate",
        )

    def test_nightly_ot(self):

        # I set the test rules to detect the number of regular and OT worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )
        self.ot_test_rule.amount_python_compute = (
            "result_rate = worked_days.OTN.rate * 100 \n"
            "result = worked_days.OTN.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for one day
        self.Attendance.create(
            {
                "employee_id": self.richard_emp.id,
                "check_in": self.localize_dt(
                    datetime.combine(start, datetime.strptime("17:00", "%H:%M").time()),
                    self.richard_emp.tz,
                    reverse=True,
                ),
                "check_out": self.localize_dt(
                    datetime.combine(start, datetime.strptime("23:00", "%H:%M").time()),
                    self.richard_emp.tz,
                    reverse=True,
                ),
            }
        )

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(
            start, end, self.richard_emp, user=self.payroll_user
        )
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Normal Test line")
        self.assertEqual(
            line[0].amount,
            5.0,
            "The number of regularly worked hours is 5",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Regular hours are paid at the normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST")
        self.assertEqual(len(line), 1, "I found the OT Test line")
        self.assertEqual(
            line[0].amount,
            1.0,
            "The number of night OT worked hours is 1",
        )
        self.assertEqual(
            line[0].rate,
            175,
            "Night OT hours are paid at 1.75x normal rate",
        )

    def test_nightly_ot_midnight(self):

        # I set the test rules to detect the number of regular and OT worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )
        self.ot_test_rule.amount_python_compute = (
            "result_rate = worked_days.OTN.rate * 100 \n"
            "result = worked_days.OTN.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for one day
        self.Attendance.create(
            {
                "employee_id": self.richard_emp.id,
                "check_in": self.localize_dt(
                    datetime.combine(start, datetime.strptime("17:00", "%H:%M").time()),
                    self.richard_emp.tz,
                    reverse=True,
                ),
                "check_out": self.localize_dt(
                    datetime.combine(
                        start + timedelta(days=1),
                        datetime.strptime("03:00", "%H:%M").time(),
                    ),
                    self.richard_emp.tz,
                    reverse=True,
                ),
            }
        )

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(
            start, end, self.richard_emp, user=self.payroll_user
        )
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Normal Test line")
        self.assertEqual(
            line[0].amount,
            5.0,
            "The number of regularly worked hours is 5",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Regular hours are paid at the normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST")
        self.assertEqual(len(line), 1, "I found the OT Test line")
        self.assertEqual(
            line[0].amount,
            5.0,
            "The number of night OT worked hours is 5",
        )
        self.assertEqual(
            line[0].rate,
            175,
            "Night OT hours are paid at 1.75x normal rate",
        )

    def test_nightly_ot_8pm5am(self):

        # I set the test rules to detect the number of regular and OT worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )
        self.ot_test_rule.amount_python_compute = (
            "result_rate = worked_days.OTN.rate * 100 \n"
            "result = worked_days.OTN.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for one day
        self.Attendance.create(
            {
                "employee_id": self.richard_emp.id,
                "check_in": self.localize_dt(
                    datetime.combine(start, datetime.strptime("20:00", "%H:%M").time()),
                    self.richard_emp.tz,
                    reverse=True,
                ),
                "check_out": self.localize_dt(
                    datetime.combine(
                        start + timedelta(days=1),
                        datetime.strptime("05:00", "%H:%M").time(),
                    ),
                    self.richard_emp.tz,
                    reverse=True,
                ),
            }
        )

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(
            start, end, self.richard_emp, user=self.payroll_user
        )
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Normal Test line")
        self.assertEqual(
            line[0].amount,
            2.0,
            "The number of regularly worked hours is 5",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Regular hours are paid at the normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST")
        self.assertEqual(len(line), 1, "I found the OT Test line")
        self.assertEqual(
            line[0].amount,
            7.0,
            "The number of night OT worked hours is 7",
        )
        self.assertEqual(
            line[0].rate,
            175,
            "Night OT hours are paid at 1.75x normal rate",
        )

    def test_ot_day_and_night(self):

        # I set the test rules to detect the number of regular and OT worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )
        self.ot_test_rule.amount_python_compute = (
            "result_rate = worked_days.OTD.rate * 100 \n"
            "result = worked_days.OTD.number_of_hours"
        )
        self.ot_test_rule2.amount_python_compute = (
            "result_rate = worked_days.OTN.rate * 100 \n"
            "result = worked_days.OTN.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for one day to include regurlar, OT, and Night OT hours
        self.Attendance.create(
            {
                "employee_id": self.richard_emp.id,
                "check_in": self.localize_dt(
                    datetime.combine(start, datetime.strptime("12:00", "%H:%M").time()),
                    self.richard_emp.tz,
                    reverse=True,
                ),
                "check_out": self.localize_dt(
                    datetime.combine(
                        start + timedelta(days=1),
                        datetime.strptime("05:00", "%H:%M").time(),
                    ),
                    self.richard_emp.tz,
                    reverse=True,
                ),
            }
        )

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(
            start, end, self.richard_emp, user=self.payroll_user
        )
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Normal Test line")
        self.assertEqual(
            line[0].amount,
            8.0,
            "The number of regularly worked hours is 8",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Regular hours are paid at the normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST")
        self.assertEqual(len(line), 1, "I found the DAY OT Test line")
        self.assertEqual(
            line[0].amount,
            2.0,
            "The number of DAY OT worked hours is 2",
        )
        self.assertEqual(
            line[0].rate,
            150,
            "DAY OT hours are paid at 1.5x normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST2")
        self.assertEqual(len(line), 1, "I found the NIGHT OT Test line")
        self.assertEqual(
            line[0].amount,
            7.0,
            "The number of NIGHT OT worked hours is 7",
        )
        self.assertEqual(
            line[0].rate,
            175,
            "NIGHT OT hours are paid at 1.75x normal rate",
        )

    def test_restday_ot(self):

        # I set the test rules to detect the number of regular and OT worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )
        self.ot_test_rule.amount_python_compute = (
            "result_rate = worked_days.OTD.rate * 100 \n"
            "result = worked_days.OTD.number_of_hours"
        )
        self.ot_test_rule2.amount_python_compute = (
            "result_rate = worked_days.OTR.rate * 100 \n"
            "result = worked_days.OTR.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for seven days
        monday = date(2022, 4, 4)
        for day in range(0, 7):
            self.Attendance.create(
                {
                    "employee_id": self.richard_emp.id,
                    "check_in": self.localize_dt(
                        datetime.combine(
                            monday + timedelta(days=day),
                            datetime.strptime("08:00", "%H:%M").time(),
                        ),
                        self.richard_emp.tz,
                        reverse=True,
                    ),
                    "check_out": self.localize_dt(
                        datetime.combine(
                            monday + timedelta(days=day),
                            datetime.strptime("17:30", "%H:%M").time(),
                        ),
                        self.richard_emp.tz,
                        reverse=True,
                    ),
                }
            )

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(
            start, end, self.richard_emp, user=self.payroll_user
        )
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Normal Test line")
        self.assertEqual(
            line[0].amount,
            48.0,
            "The number of regularly worked hours is 48",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Regular hours are paid at the normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST")
        self.assertEqual(len(line), 1, "I found the OT Test line")
        self.assertEqual(
            line[0].amount,
            9.0,
            "The number of daily OT worked hours is 9:00",
        )
        self.assertEqual(
            line[0].rate,
            150,
            "Daily OT hours are paid at 1.5x normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST2")
        self.assertEqual(len(line), 1, "I found the Rest Day OT Test line")
        self.assertEqual(
            line[0].amount,
            1.5,
            "The number of Rest Day OT worked hours is 1:30",
        )
        self.assertEqual(
            line[0].rate,
            400,
            "Rest Day OT hours are paid at 4x normal rate",
        )

    def test_holiday_ot(self):

        # I check that public holidays exist
        ph = self.PublicHoliday.search([("year", "=", 2022)])
        self.assertTrue(ph, "There is a public holiday object")
        self.assertGreater(len(ph.line_ids), 0, "At least one public holiday")

        # I set the test rules to detect the number of
        # regular, Holiday and Holiday OT worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )
        self.ot_test_rule.amount_python_compute = (
            "result_rate = worked_days.HOL.rate * 100 \n"
            "result = worked_days.HOL.number_of_hours"
        )
        self.ot_test_rule2.amount_python_compute = (
            "result_rate = worked_days.OTH.rate * 100 \n"
            "result = worked_days.OTH.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for five days
        monday = date(2022, 4, 1)
        for day in range(0, 5):
            self.Attendance.create(
                {
                    "employee_id": self.richard_emp.id,
                    "check_in": self.localize_dt(
                        datetime.combine(
                            monday + timedelta(days=day),
                            datetime.strptime("08:00", "%H:%M").time(),
                        ),
                        self.richard_emp.tz,
                        reverse=True,
                    ),
                    "check_out": self.localize_dt(
                        datetime.combine(
                            monday + timedelta(days=day),
                            datetime.strptime("17:30", "%H:%M").time(),
                        ),
                        self.richard_emp.tz,
                        reverse=True,
                    ),
                }
            )

        # I create an employee Payslip and process it
        richard_payslip = self.create_payslip(
            start, end, self.richard_emp, user=self.payroll_user
        )
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "TEST")
        self.assertEqual(len(line), 1, "I found the Normal Test line")
        self.assertEqual(
            line[0].amount,
            32.0,
            "The number of regularly worked hours is 32",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Regular hours are paid at the normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST")
        self.assertEqual(len(line), 1, "I found the OT Test line")
        self.assertEqual(
            line[0].amount,
            8.0,
            "The number of Holiday worked hours is 8:00",
        )
        self.assertEqual(
            line[0].rate,
            200,
            "Holiday hours are paid at 2x normal rate",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "OTTEST2")
        self.assertEqual(len(line), 1, "I found the Holiday OT Test line")
        self.assertEqual(
            line[0].amount,
            1.5,
            "The number of Holiday OT worked hours is 1:30",
        )
        self.assertEqual(
            line[0].rate,
            250,
            "Holiday OT hours are paid at 2.5x normal rate",
        )
