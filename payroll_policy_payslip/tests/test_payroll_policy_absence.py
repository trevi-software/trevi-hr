# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from . import common


class TestAbsencePolicy(common.TestHrPayslip):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.LeaveType = cls.env["hr.leave.type"]
        cls.LeaveRequest = cls.env["hr.leave"]
        cls.AbsencePolicy = cls.env["hr.policy.absence"]
        cls.AbsencePolicyLine = cls.env["hr.policy.line.absence"]

        # Create salary rules for Absence tests and add it to the salary structure
        cls.absence_test_rule = cls.Rule.create(
            {
                "name": "Absence test rule",
                "code": "ABTEST",
                "category_id": cls.env.ref("payroll.ALW").id,
                "sequence": 6,
                "amount_select": "code",
                "amount_python_compute": "result = 0",
            }
        )
        cls.awol_test_rule = cls.Rule.create(
            {
                "name": "AWOL test rule",
                "code": "AWTEST",
                "category_id": cls.env.ref("payroll.ALW").id,
                "sequence": 6,
                "amount_select": "code",
                "amount_python_compute": "result = 0",
            }
        )
        cls.payroll_structure.write({"rule_ids": [(4, cls.absence_test_rule.id)]})
        cls.payroll_structure.write({"rule_ids": [(4, cls.awol_test_rule.id)]})

        # Create an AWOL leave type
        cls.awol_leave_type = cls.LeaveType.create(
            {
                "name": "Absent without Leave",
                "code": "AWOL",
                "unpaid": True,
            }
        )

        # Create a Sick Leave type
        cls.sick_leave_type = cls.LeaveType.create(
            {
                "name": "Sick Leave",
                "code": "SICK50",
                "allocation_type": "no",
                "leave_validation_type": "hr",
            }
        )

        # Create an Absence Policy
        cls.absence_policy = cls.AbsencePolicy.create(
            {"name": "Absence Policy", "date": date(2000, 1, 1)}
        )
        cls.AbsencePolicyLine.create(
            {
                "name": "Line - Absent Without Leave",
                "code": "AWOL",
                "type": "dock",
                "rate": 1.0,
                "holiday_status_id": cls.awol_leave_type.id,
                "use_awol": True,
                "policy_id": cls.absence_policy.id,
            }
        )
        cls.AbsencePolicyLine.create(
            {
                "name": "Line - Sick Leave",
                "code": "SICK50",
                "type": "paid",
                "rate": 0.5,
                "holiday_status_id": cls.sick_leave_type.id,
                "policy_id": cls.absence_policy.id,
            }
        )

        # I put the absence policy in the policy group
        cls.default_policy_group.absence_policy_ids = [(4, cls.absence_policy.id)]

    def test_no_hours(self):

        # I set the test rule to detect the number of regular worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )

        # I set the test rule to detect the number of AWOL hours
        self.absence_test_rule.amount_python_compute = (
            "result_rate = worked_days.AWOL.rate * 100 \n"
            "result = worked_days.AWOL.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

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
            0.0,
            "There is no attenance",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "ABTEST")
        self.assertEqual(len(line), 1, "I found the Absence Test line")
        self.assertEqual(
            line[0].amount,
            168.0,
            "There entire month of April is AWOL",
        )
        self.assertEqual(
            line[0].rate,
            -100,
            "AWOL hours are DOCKED 100%",
        )

    def test_public_holiday_absence(self):

        # Create a public holiday
        self.public_holiday = self.PublicHoliday.create(
            {
                "year": 2022,
                "line_ids": [
                    (0, 0, {"name": "Foo", "date": date(2022, 4, 5)}),
                ],
            }
        )

        # I check that public holidays exist
        ph = self.PublicHoliday.search([("year", "=", 2022)])
        self.assertTrue(ph, "There is a public holiday object")
        self.assertGreater(len(ph.line_ids), 0, "At least one public holiday")

        # I set the test rule to detect the number of regular worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )

        # I set the test rule to detect the number of AWOL hours
        self.absence_test_rule.amount_python_compute = (
            "result_rate = worked_days.AWOL.rate * 100 \n"
            "result = worked_days.AWOL.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

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
            0.0,
            "There is no attenance",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "ABTEST")
        self.assertEqual(len(line), 1, "I found the Absence Test line")
        self.assertEqual(
            line[0].amount,
            160.0,
            "There entire month of April is AWOL minus the public holiday",
        )
        self.assertEqual(
            line[0].rate,
            -100,
            "AWOL hours are DOCKED 100%",
        )

    def test_leave_dock(self):

        # Set system parameter
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.leaves_positive", True
        )

        # Create a leave request
        lv = self.LeaveRequest.create(
            {
                "name": "Richard Sick Leave",
                "employee_id": self.richard_emp.id,
                "holiday_status_id": self.sick_leave_type.id,
                "date_from": datetime(2022, 4, 4),
                "date_to": datetime(2022, 4, 5, 23, 59, 59),
                # 'number_of_days': 2,
            }
        )
        lv.action_approve()
        self.assertEqual(lv.state, "validate", "the leave is in validate state")

        # I set the test rule to detect the number of regular worked hours
        self.test_rule.amount_python_compute = (
            "result_rate = worked_days.PL1.rate * 100 \n"
            "result = worked_days.PL1.number_of_hours"
        )

        # I set the test rule to detect the number of leave hours
        self.absence_test_rule.amount_python_compute = (
            "result_rate = worked_days.SICK50.rate * 100 \n"
            "result = worked_days.SICK50.number_of_hours"
        )

        # I set the test rule to detect the number of awol hours
        self.awol_test_rule.amount_python_compute = (
            "result_rate = worked_days.AWOL.rate * 100 \n"
            "result = worked_days.AWOL.number_of_hours"
        )

        # I create a contract for "Richard"
        contract_start = date(2022, 1, 1)
        start = date(2022, 4, 1)
        end = date(2022, 4, 30)
        self.create_contract(contract_start, False, self.richard_emp, 5000.0)
        self.apply_contract_cron()

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
            0.0,
            "There is no attenance",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "ABTEST")
        self.assertEqual(len(line), 1, "I found the Absence Test line")
        self.assertEqual(
            line[0].amount,
            16.0,
            "The time of the sick leave is recorded in worked_days",
        )
        self.assertEqual(
            line[0].rate,
            50.0,
            "The time the employee was on sick leave is paid at 0.5x",
        )

        line = richard_payslip.line_ids.filtered(lambda l: l.code == "AWTEST")
        self.assertEqual(len(line), 1, "I found the AWOL Test line")
        self.assertEqual(
            line[0].amount,
            168.0 - (2 * 8.0),
            "The time of the sick leave is not marked as AWOL",
        )
