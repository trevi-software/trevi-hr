# Copyright (C) 2025 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestHrContract(TransactionCase):
    def setUp(self):
        super().setUp()

        self.Contract = self.env["hr.contract"]
        self.Employee = self.env["hr.employee"]
        self.SalaryCode = self.env["payroll.salary.code"]

        self.code_tra = self.SalaryCode.create(
            {
                "code": "TRA",
                "description": "Transport allowance",
            }
        )
        self.code_hse = self.SalaryCode.create(
            {
                "code": "HSE",
                "description": "Housing allowance",
            }
        )

        self.employee = self.Employee.create({"name": "Test Employee"})
        self.calendar = self.env["resource.calendar"].create({"name": "Test Calendar"})

    def _create_contract(self, name="Test Contract", wage=1000):
        return self.Contract.create(
            {
                "name": name,
                "employee_id": self.employee.id,
                "resource_calendar_id": self.calendar.id,
                "wage": wage,
            }
        )

    def test_field_present(self):
        """The many2one field exists on hr.contract."""
        contract = self._create_contract()
        self.assertFalse(contract.payroll_salary_code)

    def test_assign_code(self):
        """A salary code can be assigned to and read back from a contract."""
        contract = self._create_contract()
        contract.payroll_salary_code = self.code_tra
        self.assertEqual(contract.payroll_salary_code.code, "TRA")

    def test_reassign_code(self):
        """Assigning a new code replaces the previous one."""
        contract = self._create_contract()
        contract.payroll_salary_code = self.code_tra
        contract.payroll_salary_code = self.code_hse
        self.assertEqual(contract.payroll_salary_code.code, "HSE")

    def test_multiple_contracts_share_code(self):
        """The same code can be linked to several contracts."""
        c1 = self._create_contract()
        c2 = self._create_contract(name="Test Contract 2", wage=2000)
        c1.payroll_salary_code = self.code_tra
        c2.payroll_salary_code = self.code_tra
        self.assertEqual(c1.payroll_salary_code, self.code_tra)
        self.assertEqual(c2.payroll_salary_code, self.code_tra)

    def test_unset_code(self):
        """Clearing the code from a contract doesn't delete the code itself."""
        contract = self._create_contract()
        contract.payroll_salary_code = self.code_tra
        contract.payroll_salary_code = False
        self.assertFalse(contract.payroll_salary_code)
        self.assertTrue(self.code_tra.exists())

    def test_contract_ids_one2many(self):
        """The one2many on payroll.salary.code reflects linked contracts."""
        self.assertFalse(self.code_tra.contract_ids)
        c1 = self._create_contract()
        c2 = self._create_contract(name="Test Contract 2", wage=2000)
        c1.payroll_salary_code = self.code_tra
        c2.payroll_salary_code = self.code_tra
        self.assertEqual(self.code_tra.contract_ids, c1 | c2)

    def test_one2many_unlink(self):
        """Clearing a contract's code removes it from the code's contracts."""
        contract = self._create_contract()
        contract.payroll_salary_code = self.code_tra
        self.assertIn(contract, self.code_tra.contract_ids)
        contract.payroll_salary_code = False
        self.assertNotIn(contract, self.code_tra.contract_ids)
