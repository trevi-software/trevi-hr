# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.tests import common


class TestImport(common.TransactionCase):
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

        # import_records() looks up a leave type named "Annual Leave" by
        # name; ensure it exists regardless of which demo data happens to
        # be loaded alongside this module.
        if not cls.env["hr.leave.type"].search([("name", "=", "Annual Leave")]):
            # hr_leave_type_unique adds a required 'code' field
            leave_vals = {"name": "Annual Leave", "requires_allocation": "yes"}
            if "code" in cls.env["hr.leave.type"]._fields:
                leave_vals["code"] = "ANNULV"
            cls.env["hr.leave.type"].create(leave_vals)

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
                "initial_period_date": date.today(),  # noqa: DTZ011
            }
        )
        cls.policy_group = cls.PolicyGroup.create(
            {
                "name": "Default Policy Group",
            }
        )
        cls.default_rest_day = "Friday"
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
                    "date_start": date.today(),  # noqa: DTZ011
                    "wage": 5000.00,
                    "job_id": cls.job_sales_rep.id,
                    "struct_id": cls.pay_structure.id,
                    "pps_id": cls.pps.id,
                    "policy_group_id": cls.policy_group.id,
                    "rest_day": cls.default_rest_day,
                },
                {
                    "name": "John Doe",
                    "gender": "male",
                    "birthday": date(2000, 1, 1),
                    "marital": "single",
                    "street": "456 B Avenue",
                    "private_phone": "(555) 555-666",
                    "date_start": date.today(),  # noqa: DTZ011
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
            "date_start": date.today(),  # noqa: DTZ011
            "wage": 5000.00,
            "job_id": cls.job_sales_rep.id,
            "struct_id": cls.pay_structure.id,
            "pps_id": cls.pps.id,
            "policy_group_id": cls.policy_group.id,
            "rest_day": cls.default_rest_day,
        }

    def test_workflow(self):
        self.data.action_import_employees()

        for rec in self.data:
            self.assertTrue(
                rec.related_employee_id,
                f"The created employee is linked to the data record: {rec.name}",
            )
            self.assertTrue(
                rec.related_employee_id.work_contact_id,
                f"The employee has a home address record: {rec.name}",
            )
            # In Odoo 19 a contract is an ``hr.version``.
            version = rec.related_employee_id.version_ids
            self.assertTrue(
                version,
                f"Contract created for record: {rec.name}",
            )
            self.assertEqual(
                version.contract_date_start,
                rec.date_start,
                f"Contract start date matches imported record: {rec.name}",
            )
            self.assertEqual(
                version.contract_date_end,
                rec.date_end,
                f"Contract end date matches imported record: {rec.name}",
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
            self.assertTrue(
                version.is_in_contract,
                f"Employee has a running contract: {rec.name}",
            )
            if rec.rest_day:
                self.assertIn(
                    self.default_rest_day,
                    rec.related_employee_id.resource_id.dayoff_ids.mapped("name"),
                    f"Employee's rest day matches imported record: {rec.name}",
                )
            else:
                self.assertFalse(
                    rec.related_employee_id.resource_id.dayoff_ids,
                    f"Employee's rest day is empty as no value was imported: "
                    f"{rec.name}",
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
            ee.version_id.contract_type_id,
            self.contract_type,
            f"Contract type correctly set on employee contract: {ee.name}",
        )

    def test_set_value_contract_trial_end_date(self):
        vals = dict(
            self.sample01,
            trial_date_end=date.today() + timedelta(days=15),  # noqa: DTZ011
        )
        data = self.DataImport.create(vals)
        data.import_records()
        ee = self.Employee.search([("name", "=", data[0].name)])
        self.assertTrue(ee, f"Found employee: {data[0].name}")
        self.assertEqual(
            ee.version_id.trial_date_end,
            date.today() + timedelta(days=15),  # noqa: DTZ011
            f"Trial end date correctly set on employee contract: {ee.name}",
        )

    def test_set_value_calendar(self):
        self.data[0].resource_calendar_id = self.std_calendar
        self.data.import_records()
        ee = self.Employee.search([("name", "=", self.data[0].name)])
        self.assertTrue(ee, f"Found employee: {self.data[0].name}")
        self.assertEqual(
            ee.version_id.resource_calendar_id,
            self.std_calendar,
            f"Calendar correctly set on employee contract: {ee.name}",
        )

    def test_rest_day(self):
        self.data[1].rest_day = self.default_rest_day
        self.data.import_records()
        ee = self.Employee.search([("name", "=", self.data[1].name)])
        self.assertTrue(ee, f"Found employee: {self.data[1].name}")
        self.assertIn(
            self.default_rest_day,
            ee.resource_id.dayoff_ids.mapped("name"),
            f"Calendar correctly set on employee contract: {ee.name}",
        )

    def test_annual_leave_allocation(self):
        LeaveType = self.env["hr.leave.type"].with_context(tracking_disable=True)
        vals = {"name": "Annual Leave"}
        if "code" in LeaveType._fields:
            vals["code"] = "ANLV"
        LeaveType.create(vals)
        vals = dict(self.sample01, anlv_earned=20.0, anlv_used=5.0)
        data = self.DataImport.create(vals)
        data.import_records()
        ee = self.Employee.search([("name", "=", data[0].name)])
        allocation = self.env["hr.leave.allocation"].search(
            [("employee_id", "=", ee.id)]
        )
        self.assertTrue(allocation, f"Leave allocation created for record: {ee.name}")
        self.assertEqual(
            allocation.number_of_days,
            15.0,
            "Allocated days is the difference between earned and used leave",
        )
        self.assertEqual(
            allocation.state,
            "validate",
            "Leave allocation is confirmed and validated",
        )

    def test_import_uses_row_company(self):
        """The employee, its contact and contract belong to the row's company.

        Regression: the import used the active company instead of the one
        stored on the import row.
        """
        company = self.env["res.company"].create(
            {"name": "Second Company", "country_id": self.env.ref("base.et").id}
        )
        vals = dict(self.sample01, name="Company Bee", company_id=company.id)
        data = self.DataImport.with_company(company).create(vals)
        data.import_records()
        ee = data.related_employee_id
        self.assertEqual(ee.company_id, company)
        self.assertEqual(ee.version_id.company_id, company)
        self.assertEqual(ee.work_contact_id.company_id, company)

    def test_update_new_row_is_rejected(self):
        """A new row cannot be "updated": it has no employee to update.

        Regression: updating a new row set its state to "updated", so the
        following import rejected it and the row could never be imported.
        """
        data = self.DataImport.create(dict(self.sample01, name="Not Imported Yet"))
        with self.assertRaises(UserError):
            data.action_update_employees()
        self.assertEqual(data.state, "new", "The row is still importable")
        self.assertFalse(data.related_employee_id)

        data.action_import_employees()
        self.assertTrue(
            data.related_employee_id,
            "The row can still be imported after a rejected update",
        )
        self.assertEqual(data.state, "imported")

    def test_import_rows_restricted_to_user_companies(self):
        """An HR user only reads the import rows of their allowed companies.

        Regression: the ACL granted read access with no company record rule,
        so an HR user of one company could read another company's wages and
        identification numbers.
        """
        company_a = self.env.company
        company_b = self.env["res.company"].create({"name": "Other Company"})
        other_row = self.DataImport.with_company(company_b).create(
            dict(
                self.sample01,
                name="Other Company Row",
                company_id=company_b.id,
                wage=9999.0,
                identification_id="B-123456",
            )
        )
        own_row = self.DataImport.with_company(company_a).create(
            dict(self.sample01, name="Own Company Row", company_id=company_a.id)
        )

        groups = self.env.ref("base.group_user") | self.env.ref("hr.group_hr_user")
        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "HR User Company A",
                    "login": "hr_user_company_a",
                    "email": "hr_user_company_a@example.com",
                    "company_id": company_a.id,
                    "company_ids": [(6, 0, [company_a.id])],
                    "group_ids": [(6, 0, groups.ids)],
                }
            )
        )

        visible = self.DataImport.with_user(user).search([])
        self.assertIn(own_row, visible, "The user reads their own company's rows")
        self.assertNotIn(other_row, visible, "Another company's rows are hidden")

    def test_zero_balance_does_not_require_annual_leave_type(self):
        """An import without a leave balance must not need an 'Annual Leave'.

        Regression: the leave type lookup was done before knowing whether any
        allocation was needed, so a zero-balance import failed on it.
        """
        leave_type = self.env["hr.leave.type"].search(
            [("name", "=", "Annual Leave")], limit=1
        )
        leave_type.name = "Not Annual Leave"
        data = self.DataImport.create(self.sample01)
        data.import_records()
        self.assertTrue(
            data.related_employee_id,
            "The employee was created without an annual leave type",
        )
        self.assertFalse(
            self.env["hr.leave.allocation"].search(
                [("employee_id", "=", data.related_employee_id.id)]
            ),
            "No leave allocation is created for a zero balance",
        )

    def test_update_replaces_previous_rest_day(self):
        """Updating the rest day replaces the imported one, keeping other days.

        Regression: the previously imported day was left in ``dayoff_ids``, so
        the employee ended up with two days off.
        """
        vals = dict(self.sample01, name="Rest Day Person", rest_day="Friday")
        data = self.DataImport.create(vals)
        # Use the public import action: a row must be imported (its state
        # leaves "new") before it can be updated.
        data.action_import_employees()
        ee = data.related_employee_id
        resource = ee.resource_id
        self.assertEqual(resource.dayoff_ids.mapped("name"), ["Friday"])

        monday = self.env.ref("resource_schedule.wd_mon")
        resource.dayoff_ids = [(4, monday.id)]
        data.rest_day = "Saturday"
        data.action_update_employees()

        names = resource.dayoff_ids.mapped("name")
        self.assertNotIn("Friday", names, "The previous imported rest day is removed")
        self.assertIn("Saturday", names, "The new rest day is added")
        self.assertIn("Monday", names, "Unrelated days off are preserved")

    def test_imported_department_used_without_job(self):
        """A row with a department and no job still sets the department.

        Regression: the department was taken from the job only.
        """
        vals = dict(
            self.sample01,
            name="Department Only",
            department_id=self.dept_sales.id,
            job_id=False,
        )
        data = self.DataImport.create(vals)
        data.import_records()
        ee = data.related_employee_id
        self.assertEqual(ee.department_id, self.dept_sales)
        self.assertEqual(ee.version_id.department_id, self.dept_sales)

    def test_department_falls_back_to_job(self):
        """Without an imported department the job's department is used."""
        vals = dict(self.sample01, name="Job Only", department_id=False)
        data = self.DataImport.create(vals)
        data.import_records()
        ee = data.related_employee_id
        self.assertEqual(ee.department_id, self.dept_sales)

    def test_education_level_certificates(self):
        """The imported education levels map onto certificate levels.

        Regression: 'Diploma' and 'BA Degree' were compared with values that
        do not exist and 'Masters Degree' had no branch at all, so the value
        was silently dropped.
        """
        expected = {
            "Diploma": "other",
            "BA Degree": "bachelor",
            "Masters Degree": "master",
        }
        for level, certificate in expected.items():
            data = self.DataImport.create(
                dict(
                    self.sample01,
                    name=f"Education {level}",
                    education_level=level,
                )
            )
            data.import_records()
            self.assertEqual(
                data.related_employee_id.certificate,
                certificate,
                f"Certificate level set for imported education level: {level}",
            )
