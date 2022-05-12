# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.payroll.tests.common import TestPayslipBase


def get_localdict_mock(*args, **kwargs):
    return {"mock": True}


def get_contractdict_mock(*args, **kwargs):
    return {"my_mock_value": True}


class TestPayslip(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.Contract = self.env["hr.contract"]
        self.HrPayslip = self.env["hr.payslip"]
        self.Rule = self.env["hr.salary.rule"]

        self.mock_rule = self.Rule.create(
            {
                "name": "Mock Salary Rule",
                "code": "MOCK",
                "sequence": 5,
                "category_id": self.ref("payroll.ALW"),
                "amount_select": "code",
                "amount_python_compute": "result = (dictionaries.mock is True) and 1.0 or 0.0",
            }
        )
        self.developer_pay_structure.write(
            {"parent_id": self.ref("payroll.structure_base")}
        )
        self.developer_pay_structure.write({"rule_ids": [(4, self.mock_rule.id)]})

        contracts = self.Contract.search([("employee_id", "=", self.richard_emp.id)])
        contracts[0].kanban_state = "done"

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def test_localdict(self):

        self.apply_contract_cron()

        # I create an employee Payslip
        richard_payslip = self.env["hr.payslip"].create(
            {"name": "Payslip of Richard", "employee_id": self.richard_emp.id}
        )

        # I patch the get_localdict() method to return my own dictionary
        richard_payslip._patch_method("get_localdict", get_localdict_mock)
        richard_payslip.compute_sheet()

        mock_payslip_line = False
        for line in richard_payslip.line_ids:
            if line.code == "MOCK":
                mock_payslip_line = line
        self.assertTrue(mock_payslip_line, "The mock payslip rule was processed")
        self.assertEqual(
            mock_payslip_line.amount, 1.0, "The mock payslip rule was evaluated"
        )

    def test_contractdict(self):

        self.apply_contract_cron()
        self.mock_rule.amount_python_compute = (
            "result = (this_contract.my_mock_value is True) and 1.0 or 0.0"
        )

        # I create an employee Payslip
        richard_payslip = self.env["hr.payslip"].create(
            {"name": "Payslip of Richard", "employee_id": self.richard_emp.id}
        )

        # I patch the get_localdict() method to return my own dictionary
        richard_payslip._patch_method("get_contractdict", get_contractdict_mock)
        richard_payslip.compute_sheet()

        mock_payslip_line = False
        for line in richard_payslip.line_ids:
            if line.code == "MOCK":
                mock_payslip_line = line
        self.assertTrue(
            mock_payslip_line, "The mock payslip contract rule was processed"
        )
        self.assertEqual(
            mock_payslip_line.amount,
            1.0,
            "The mock payslip contract rule was evaluated",
        )
