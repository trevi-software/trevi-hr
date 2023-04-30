# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.tests import common


class TestImport(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.DataImport = cls.env["hr.data.import.employee"]
        cls.Department = cls.env["hr.department"]
        cls.Employee = cls.env["hr.employee"]
        cls.Job = cls.env["hr.job"]
        cls.PayrollStructure = cls.env["hr.payroll.structure"]
        cls.PolicyGroup = cls.env["hr.policy.group"]
        cls.Schedule = cls.env["hr.payroll.period.schedule"]
        cls.SalaryRule = cls.env["hr.salary.rule"]
        cls.SalaryRuleCateg = cls.env["hr.salary.rule.category"]

        # Payroll related
        #
        cls.categ_basic = cls.SalaryRuleCateg.create(
            {
                "name": "Basic",
                "code": "BASIC",
            }
        )
        cls.rule_basic = cls.SalaryRule.create(
            {
                "name": "Basic Salary",
                "code": "BASIC",
                "sequence": 1,
                "category_id": cls.categ_basic.id,
                "condition_select": "none",
                "amount_select": "code",
                "amount_python_compute": "result = contract.wage",
            }
        )
        cls.pay_structure = cls.PayrollStructure.create(
            {
                "name": "Basic Salary Structure",
                "code": "BSS",
                "company_id": cls.env.ref("base.main_company").id,
                "rule_ids": [
                    (4, cls.rule_basic.id),
                ],
            }
        )

        cls.std_calendar = cls.env["resource.calendar"].create({"name": "Std"})
        cls.contract_type = cls.env["hr.contract.type"].create({"name": "Permanent"})
        cls.dept_sales = cls.Department.create({"name": "Sales"})
        cls.job_sales_rep = cls.Job.create(
            {"name": "Sales Rep", "department_id": cls.dept_sales.id}
        )
        cls.pps = cls.Schedule.create(
            {
                "name": "PPS",
                "tz": "Africa/Addis_Ababa",
                "type": "manual",
                "initial_period_date": date.today(),
            }
        )
        cls.policy_group = cls.PolicyGroup.create(
            {
                "name": "Default Policy Group",
            }
        )
        cls.data = cls.DataImport.create(
            [
                {
                    "name": "Sally Ford",
                    "gender": "female",
                    "street": "123 A Avenue",
                    "private_phone": "(555) 555-5555",
                    "emergency_contact": "John Doe",
                    "emergency_phone": "(555) 555-666",
                    "hire_date": date(2000, 1, 1),
                    "date_start": date.today(),
                    "wage": 5000.00,
                    "job_id": cls.job_sales_rep.id,
                    "struct_id": cls.pay_structure.id,
                    "pps_id": cls.pps.id,
                    "policy_group_id": cls.policy_group.id,
                },
                {
                    "name": "John Doe",
                    "gender": "male",
                    "birthday": date(2000, 1, 1),
                    "marital": "single",
                    "street": "456 B Avenue",
                    "private_phone": "(555) 555-666",
                    "date_start": date.today(),
                    "wage": 4000.00,
                    "job_id": cls.job_sales_rep.id,
                    "struct_id": cls.pay_structure.id,
                    "pps_id": cls.pps.id,
                    "policy_group_id": cls.policy_group.id,
                },
            ]
        )

        cls.sample01 = {
            "name": "Alice",
            "gender": "female",
            "street": "123 A Avenue",
            "private_phone": "(555) 555-5555",
            "emergency_contact": "John Doe",
            "emergency_phone": "(555) 555-666",
            "hire_date": date(2000, 1, 1),
            "date_start": date.today(),
            "wage": 5000.00,
            "job_id": cls.job_sales_rep.id,
            "struct_id": cls.pay_structure.id,
            "pps_id": cls.pps.id,
            "policy_group_id": cls.policy_group.id,
        }

    def test_workflow(self):
        self.data.action_import_employees()

        for rec in self.data:
            self.assertTrue(
                rec.related_employee_id,
                f"The created employee is linked to the data record: {rec.name}",
            )
            self.assertTrue(
                rec.related_employee_id.address_home_id,
                f"The employee has a home address record: {rec.name}",
            )
            self.assertEqual(
                rec.related_employee_id.address_home_id.type,
                "private",
                f"The employee home address contact type is private: {rec.name}",
            )
            self.assertTrue(
                rec.related_employee_id.contract_ids.ids,
                f"Contract created for record: {rec.name}",
            )
            if rec.identification_id:
                self.assertEqual(
                    rec.related_employee_id.identification_id,
                    rec.identification_id,
                    "Employee government ID matches imported record",
                )
            if rec.private_email:
                self.assertEqual(
                    rec.related_employee_id.private_email,
                    rec.private_email,
                    "Employee private email matches imported record",
                )
            if rec.emergency_contact:
                self.assertEqual(
                    rec.related_employee_id.emergency_contact,
                    rec.emergency_contact,
                    "Employee emergency contact matches imported record",
                )
            if rec.emergency_phone:
                self.assertEqual(
                    rec.related_employee_id.emergency_phone,
                    rec.emergency_phone,
                    "Employee emergency contact phone matches imported record",
                )
            if rec.hire_date:
                self.assertEqual(
                    rec.related_employee_id.contract_ids[0].state,
                    "open",
                    f"Employee's contract is in 'open' state: {rec.name}",
                )
            else:
                self.assertEqual(
                    rec.related_employee_id.contract_ids[0].state,
                    "trial",
                    f"Employee's contract is in 'trial' state: {rec.name}",
                )
            self.assertEqual(
                rec.state,
                "imported",
                f"The record state is 'imported' after employee creation: {rec.name}",
            )

        # Attempt to import again raises exception
        with self.assertRaises(UserError):
            self.data.action_import_employees()

    def test_set_value_contract_type(self):
        self.data[0].contract_type_id = self.contract_type
        self.data.import_records()
        ee = self.Employee.search([("name", "=", self.data[0].name)])
        self.assertTrue(ee, f"Found employee: {self.data[0].name}")
        self.assertEqual(
            ee.contract_ids[0].contract_type_id,
            self.contract_type,
            f"Contract type correctly set on employee contract: {ee.name}",
        )

    def test_set_value_contract_trial_end_date(self):
        self.sample01.update({"trial_date_end": date.today() + timedelta(days=15)})
        data = self.DataImport.create(self.sample01)
        data.import_records()
        ee = self.Employee.search([("name", "=", data[0].name)])
        self.assertTrue(ee, f"Found employee: {data[0].name}")
        self.assertEqual(
            ee.contract_ids[0].trial_date_end,
            date.today() + timedelta(days=15),
            f"Trial end date correctly set on employee contract: {ee.name}",
        )

    def test_set_value_calendar(self):
        self.data[0].resource_calendar_id = self.std_calendar
        self.data.import_records()
        ee = self.Employee.search([("name", "=", self.data[0].name)])
        self.assertTrue(ee, f"Found employee: {self.data[0].name}")
        self.assertEqual(
            ee.contract_ids[0].resource_calendar_id,
            self.std_calendar,
            f"Calendar correctly set on employee contract: {ee.name}",
        )
