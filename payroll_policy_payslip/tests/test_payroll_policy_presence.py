# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from . import common


class TestPresencePolicy(common.TestHrPayslip):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a public holiday
        cls.public_holiday = cls.PublicHoliday.create(
            {
                "year": 2022,
                "line_ids": [
                    (0, 0, {"name": "Foo", "date": date(2022, 4, 2)}),
                ],
            }
        )

    def test_worked_hours(self):

        # I set the test rule to detect the number of regular worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
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
                "check_in": datetime.combine(
                    start, datetime.strptime("08:00", "%H:%M").time()
                ),
                "check_out": datetime.combine(
                    start, datetime.strptime("16:00", "%H:%M").time()
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
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(
            line[0].amount,
            8.0,
            "The number of worked hours is 8",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Regular hours are paid at the normal rate",
        )

    def test_worked_holiday(self):

        # I check that public holidays exist
        ph = self.PublicHoliday.search([("year", "=", 2022)])
        self.assertTrue(ph, "There is a public holiday object")
        self.assertGreater(len(ph.line_ids), 0, "At least one public holiday")

        # I set the test rule to detect the number of holiday worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.HOL.rate * 100 \n"
            "result = worked_days.HOL.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance on a public holiday
        self.Attendance.create(
            {
                "employee_id": self.richard_emp.id,
                "check_in": datetime.combine(
                    start + timedelta(days=1),
                    datetime.strptime("08:00", "%H:%M").time(),
                ),
                "check_out": datetime.combine(
                    start + timedelta(days=1),
                    datetime.strptime("16:00", "%H:%M").time(),
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
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(
            line[0].amount,
            8.0,
            "The number of worked holiday hours is 8",
        )
        self.assertEqual(
            line[0].rate,
            200,
            "Holiday hours are paid double",
        )

    def test_worked_restday(self):

        # I set the test rule to detect the number of rest day worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.RST.rate * 100 \n"
            "result = worked_days.RST.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for seven days in a row
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
                            datetime.strptime("16:00", "%H:%M").time(),
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
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(
            line[0].amount,
            8.0,
            "The number of worked rest day hours is 8 (1 day)",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Rest day hours are accrued at the regular rate",
        )

    def test_worked_restday_weekend(self):

        # I set the weekly working days to 5
        self.presence_policy.work_days_per_week = 5

        # I set the test rule to detect the number of rest day worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.RST.rate * 100 \n"
            "result = worked_days.RST.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

        # I create attendance for eight days in a row
        monday = date(2022, 4, 4)
        for day in range(0, 8):
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
                            datetime.strptime("16:00", "%H:%M").time(),
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
        self.assertEqual(len(line), 1, "I found the Test line")
        self.assertEqual(
            line[0].amount,
            16.0,
            "The number of worked rest day hours is 16 (2 days)",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Rest day hours are accrued at the regular rate",
        )
