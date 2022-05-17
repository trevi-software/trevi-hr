# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestHrPayslip(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.Contract = self.env["hr.contract"]
        self.HrPayslip = self.env["hr.payslip"]
        self.Rule = self.env["hr.salary.rule"]

        self.resource_calendar_std = self.env.ref("resource.resource_calendar_std")
        self.payroll_structure = self.env.ref("payroll.structure_base")
        self.basic_salary_rule = self.env.ref("payroll.hr_rule_basic")
        self.basic_salary_rule.amount_python_compute = (
            "result = contract.wage * this_contract.ppf"
        )

        # I create a new employee "Richard"
        self.richard_emp = self.env["hr.employee"].create(
            {
                "name": "Richard",
                "gender": "male",
                "birthday": "1984-05-01",
                "country_id": self.ref("base.be"),
                "department_id": self.ref("hr.dep_rd"),
                "resource_calendar_id": self.resource_calendar_std.id,
            }
        )

        self.test_rule = self.Rule.create(
            {
                "name": "Test rule",
                "code": "TEST",
                "category_id": self.ref("payroll.ALW"),
                "sequence": 5,
                "amount_select": "code",
                "amount_python_compute": "result=contract.wage",
            }
        )
        self.payroll_structure.write({"rule_ids": [(4, self.test_rule.id)]})

    def create_contract(self, start, end, employee, wage, name=False):
        return self.Contract.create(
            {
                "date_start": start,
                "date_end": end,
                "name": name if name else f"Contract for {employee.name}",
                "wage": wage,
                "employee_id": employee.id,
                "struct_id": self.payroll_structure.id,
                "kanban_state": "done",
            }
        )

    def create_payslip(self, start, end, employee):

        return self.HrPayslip.create(
            {
                "name": f"Payslip of {employee.name}",
                "employee_id": employee.id,
                "date_from": start,
                "date_to": end,
            }
        )

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()
