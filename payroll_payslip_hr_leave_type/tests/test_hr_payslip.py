# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, time

from dateutil.relativedelta import relativedelta

from odoo.addons.payroll.tests.common import TestPayslipBase


class TestHrPayslip(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.Contract = self.env["hr.contract"]
        self.HrPayslip = self.env["hr.payslip"]
        self.Rule = self.env["hr.salary.rule"]
        self.Requests = self.env["hr.leave"]
        self.HolidaysStatus = self.env["hr.leave.type"]

        # create holiday type
        self.holiday_type = self.HolidaysStatus.create(
            {
                "name": "TestLeaveType",
                "code": "TESTLV",
                "allocation_type": "no",
                "leave_validation_type": "no_validation",
            }
        )

        self.basic_rule = self.env.ref("payroll.hr_rule_basic")
        self.basic_rule.amount_python_compute = "result = contract.wage"
        self.mock_rule = self.Rule.create(
            {
                "name": "Leave Salary Rule",
                "code": "TESTLV",
                "sequence": 5,
                "category_id": self.ref("payroll.ALW"),
                "condition_select": "python",
                "condition_python": "result = 0",
                "amount_select": "code",
                "amount_python_compute": "result = 1000.0",
            }
        )
        self.developer_pay_structure.write(
            {"parent_id": self.ref("payroll.structure_base")}
        )
        self.developer_pay_structure.write({"rule_ids": [(4, self.mock_rule.id)]})

        self.resource_calendar_std = self.env.ref("resource.resource_calendar_std")
        contracts = self.Contract.search([("employee_id", "=", self.richard_emp.id)])
        contracts[0].resource_calendar_id = self.resource_calendar_std
        contracts[0].kanban_state = "done"
        contracts[0].date_start = datetime(2022, 1, 1)

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def test_holiday_type_code(self):

        self.mock_rule.condition_python = "result = worked_days.LVCODE"
        self.mock_rule.amount_python_compute = (
            "result = worked_days.LVCODE.number_of_days"
        )

        self.apply_contract_cron()
        self.assertEqual(
            self.richard_emp.contract_id.state, "open", "Contract is in 'open' state"
        )

        # Set system parameter
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.leaves_positive", True
        )

        # Create a leave request
        lv_from = datetime.combine(datetime.today(), time.min)
        lv_to = datetime.combine(datetime.today(), time.max)
        while lv_from.date().weekday() in [5, 6]:
            lv_from -= relativedelta(days=1)
        while lv_to.date().weekday() in [5, 6]:
            lv_to -= relativedelta(days=1)
        leave = self.Requests.create(
            {
                "name": "Hol11",
                "employee_id": self.richard_emp.id,
                "holiday_status_id": self.holiday_type.id,
                "date_from": lv_from,
                "date_to": lv_to,
                "number_of_days": 1,
            }
        )
        self.assertEqual(
            leave.state, "validate", "newly created leave request is in validate state"
        )

        # I create an employee Payslip and process it
        richard_payslip = self.env["hr.payslip"].create(
            {"name": "Payslip of Richard", "employee_id": self.richard_emp.id}
        )
        richard_payslip.onchange_employee()
        richard_payslip.compute_sheet()

        worked_days_line = richard_payslip.worked_days_line_ids.filtered(
            lambda l: l.code == "TESTLV"
        )
        self.assertEqual(
            len(worked_days_line), 1, "There is a worked_days_line for the leave"
        )
        self.assertEqual(
            worked_days_line.number_of_days,
            1.0,
            "The number of days for the leave is the same as the holiday request",
        )
        self.assertEqual(
            len(
                richard_payslip.worked_days_line_ids.filtered(
                    lambda l: l.code == "WORK100"
                )
            ),
            1,
            "The 'WORK100' worked days line is still there",
        )
