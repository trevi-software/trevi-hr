# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.addons.payroll.tests.common import TestPayslipBase


class TestHrPayslip(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.resource_calendar_std = self.env.ref("resource.resource_calendar_std")

        # I modify the 'BASIC' salary rule to take into
        # consideration the Payroll Period Factor
        self.rule_basic.amount_python_compute = (
            "result = contract.wage * current_contract.ppf"
        )

        # I create a simple salary structure
        self.basic_pay_structure = self.PayrollStructure.create(
            {
                "name": "Salary Structure Basic",
                "code": "BC",
                "company_id": self.ref("base.main_company"),
                "rule_ids": [
                    (4, self.rule_basic.id),
                    (4, self.rule_gross.id),
                    (4, self.rule_net.id),
                ],
            }
        )
        self.test_rule = self.SalaryRule.create(
            {
                "name": "Test rule",
                "code": "TEST",
                "category_id": self.categ_alw.id,
                "sequence": 5,
                "amount_select": "code",
                "amount_python_compute": "result=contract.wage",
            }
        )
        self.basic_pay_structure.write({"rule_ids": [(4, self.test_rule.id)]})

        # I create a new employee "Sally"
        self.alice_emp = self.env["hr.employee"].create(
            {
                "name": "Sally",
                "gender": "female",
                "birthday": "1984-05-01",
                "country_id": self.ref("base.be"),
                "department_id": self.dept_rd.id,
            }
        )

        self.month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def leap_year(self, y):
        if y % 400 == 0:
            return True
        if y % 100 == 0:
            return False
        if y % 4 == 0:
            return True
        else:
            return False

    def create_contract(self, start, end, employee, wage, name=False):
        return self.Contract.create(
            {
                "date_start": start,
                "date_end": end,
                "name": name if name else f"Contract for {employee.name}",
                "wage": wage,
                "employee_id": employee.id,
                "struct_id": self.basic_pay_structure.id,
                "kanban_state": "done",
                "resource_calendar_id": self.resource_calendar_std.id,
            }
        )

    def create_payslip(self, start, end, employee):

        return self.Payslip.create(
            {
                "name": f"Payslip of {employee.name}",
                "employee_id": employee.id,
                "date_from": start,
                "date_to": end,
            }
        )
