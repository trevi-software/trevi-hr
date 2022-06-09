# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from . import common


class TestPresencePolicy(common.TestHrPayslip):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Attendance = cls.env["hr.attendance"]
        cls.PublicHoliday = cls.env["hr.holidays.public"]
        cls.PresencePolicy = cls.env["hr.policy.presence"]
        cls.PresencePolicyLine = cls.env["hr.policy.line.presence"]
        cls.presence_policy = cls.PresencePolicy.create(
            {"name": "POLICY1", "date": date(2000, 1, 1)}
        )
        cls.PresencePolicyLine.create(
            {
                "name": "Presence Line - Normal workday",
                "code": "PL1",
                "type": "normal",
                "active_after": 0.0,
                "duration": 8.0 * 60,
                "policy_id": cls.presence_policy.id,
            }
        )
        cls.PresencePolicyLine.create(
            {
                "name": "Presence Line - Holiday",
                "code": "HOL",
                "type": "holiday",
                "active_after": 0.0,
                "duration": 8.0 * 60,
                "rate": 2.0,
                "policy_id": cls.presence_policy.id,
            }
        )
        cls.PresencePolicyLine.create(
            {
                "name": "Presence Line - Rest day",
                "code": "RST",
                "type": "restday",
                "active_after": 0.0,
                "duration": 8.0 * 60,
                "rate": 1.0,
                "policy_id": cls.presence_policy.id,
            }
        )

        # I put the presence policy in the policy group
        cls.default_policy_group.presence_policy_ids = [(4, cls.presence_policy.id)]

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

        # I create attendance on a day off (Saturday April 9, 2022)
        self.Attendance.create(
            {
                "employee_id": self.richard_emp.id,
                "check_in": datetime.combine(
                    start + timedelta(days=8),
                    datetime.strptime("08:00", "%H:%M").time(),
                ),
                "check_out": datetime.combine(
                    start + timedelta(days=8),
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
            "The number of worked rest day hours is 8",
        )
        self.assertEqual(
            line[0].rate,
            100,
            "Rest day hours are accrued at the regular rate",
        )
