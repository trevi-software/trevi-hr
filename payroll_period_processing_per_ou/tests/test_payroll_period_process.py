# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from odoo.addons.mail.tests.common import mail_new_test_user
from odoo.addons.payroll_period_processing.tests.test_payroll_period_process import (
    TestProcessing,
)


class TestProcessingOU(TestProcessing):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.OU = cls.env["operating.unit"]
        cls.Register = cls.env["hr.payroll.register"]

        cls.admin_dept = cls.Department.create(
            {
                "name": "Administration",
            }
        )
        cls.job_hradmin = cls.env["hr.job"].create(
            {
                "name": "HR Admin",
                "department_id": cls.admin_dept.id,
            }
        )

        # Operating Units
        cls.ou_main = cls.OU.create(
            {"name": "Main", "code": "M", "partner_id": cls.env.company.id}
        )
        cls.ou_second = cls.OU.create(
            {"name": "Second", "code": "S", "partner_id": cls.env.company.id}
        )
        cls.all_ou_ids = cls.OU.sudo().search([])

        cls.user_sally = mail_new_test_user(
            cls.env, login="sally", groups="base.group_user,payroll.group_payroll_user"
        )
        cls.user_marry = mail_new_test_user(
            cls.env,
            login="marry",
            groups="base.group_user,"
            "payroll.group_payroll_user,"
            "payroll_period_processing_per_ou.group_all_ou_periods",
        )
        cls.user_employee.default_operating_unit_id = cls.ou_main
        cls.user_employee.operating_unit_ids = cls.ou_main
        cls.user_sally.default_operating_unit_id = cls.ou_second
        cls.user_sally.operating_unit_ids = cls.ou_second
        cls.employee_emp.default_operating_unit_id = cls.ou_main
        cls.employee_sally = cls.Employee.create(
            {"name": "Sally", "default_operating_unit_id": cls.ou_second.id}
        )
        cls.payrollOfficer.operating_unit_ids = cls.all_ou_ids
        cls.payrollOfficer.write(
            {
                "groups_id": [
                    (
                        4,
                        cls.env.ref(
                            "payroll_period_processing_per_ou.group_all_ou_periods"
                        ).id,
                    )
                ]
            }
        )

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def test_ou_access(self):

        cc1 = self.create_contract(
            self.employee_emp.id, "draft", "done", date(2021, 1, 1)
        )
        cc2 = self.create_contract(
            self.employee_sally.id, "draft", "done", date(2021, 1, 1)
        )
        cc1.operating_unit_id = self.ou_main
        cc2.operating_unit_id = self.ou_second
        self.apply_contract_cron()
        start = datetime(2021, 9, 1)
        schedule = self.create_payroll_schedule("monthly", start.date())
        schedule.use_operating_units = True
        schedule.add_pay_period()
        ou_ids = self.OU.search([])
        self.assertEqual(
            len(schedule.pay_period_ids), len(ou_ids), "There is one pay period per OU"
        )

        emp_pp_ids = self.Period.with_user(self.user_employee.id).search([])
        sally_pp_ids = self.Period.with_user(self.user_sally.id).search([])
        officer_pp_ids = self.Period.with_user(self.payrollOfficer.id).search([])
        self.assertEqual(
            len(emp_pp_ids), 1, "There is only 1 payperiod 'user_employee' can see"
        )
        self.assertEqual(
            emp_pp_ids.operating_unit_id,
            self.ou_main,
            "User 'user_employee' has access to OU %s" % self.ou_main.name,
        )
        self.assertEqual(
            len(sally_pp_ids), 1, "There is only 1 payperiod 'user_sally' can see"
        )
        self.assertEqual(
            sally_pp_ids.operating_unit_id,
            self.ou_second,
            "User 'user_sally' has access to OU %s" % self.ou_second.name,
        )
        self.assertEqual(
            self.all_ou_ids,
            officer_pp_ids.mapped("operating_unit_id"),
            "Payroll Officer has access to all pay periods from all OUs",
        )

    def test_register_access(self):

        cc1 = self.create_contract(
            self.employee_emp.id, "draft", "done", date(2021, 1, 1)
        )
        cc2 = self.create_contract(
            self.employee_sally.id, "draft", "done", date(2021, 1, 1)
        )
        cc1.operating_unit_id = self.ou_main
        cc2.operating_unit_id = self.ou_second
        self.apply_contract_cron()
        start = datetime(2021, 9, 1)
        schedule = self.create_payroll_schedule("monthly", start.date())
        schedule.use_operating_units = True
        schedule.add_pay_period()
        self.user_employee.write(
            {"groups_id": [(4, self.env.ref("payroll.group_payroll_user").id)]}
        )
        self.user_sally.write(
            {"groups_id": [(4, self.env.ref("payroll.group_payroll_user").id)]}
        )

        # Process each period
        for period in schedule.pay_period_ids:
            wiz = (
                self.Wizard.with_user(self.payrollOfficer)
                .with_context({"active_id": period.id})
                .create({})
            )
            wiz.create_payroll_register()

        emp_reg_ids = self.Register.with_user(self.user_employee.id).search([])
        sally_reg_ids = self.Register.with_user(self.user_sally.id).search([])
        officer_reg_ids = self.Register.with_user(self.payrollOfficer.id).search([])
        self.assertEqual(
            len(emp_reg_ids), 1, "There is only 1 register 'user_employee' can see"
        )
        self.assertEqual(
            emp_reg_ids.operating_unit_id,
            self.ou_main,
            "User 'user_employee' has access to register in OU %s" % self.ou_main.name,
        )
        self.assertEqual(
            len(sally_reg_ids), 1, "There is only 1 register 'user_sally' can see"
        )
        self.assertEqual(
            sally_reg_ids.operating_unit_id,
            self.ou_second,
            "User 'user_sally' has access to register in OU %s" % self.ou_second.name,
        )
        self.assertEqual(
            self.all_ou_ids,
            officer_reg_ids.mapped("operating_unit_id"),
            "Payroll Officer has access to all registers from all OUs",
        )

    def test_register_contracts(self):

        cc1 = self.create_contract(
            self.employee_emp.id, "draft", "done", date(2021, 1, 1)
        )
        cc2 = self.create_contract(
            self.employee_sally.id, "draft", "done", date(2021, 1, 1)
        )
        cc1.operating_unit_id = self.ou_main
        cc2.operating_unit_id = self.ou_second
        start = datetime(2021, 9, 1)
        schedule = self.create_payroll_schedule("monthly", start.date())
        schedule.use_operating_units = True
        schedule.add_pay_period()
        self.user_employee.write(
            {"groups_id": [(4, self.env.ref("payroll.group_payroll_user").id)]}
        )
        self.user_sally.write(
            {"groups_id": [(4, self.env.ref("payroll.group_payroll_user").id)]}
        )

        # Process each period
        for period in schedule.pay_period_ids:
            wiz = (
                self.Wizard.with_user(self.payrollOfficer)
                .with_context({"active_id": period.id})
                .create({})
            )
            wiz.create_payroll_register()
            for contract in wiz.contract_ids:
                self.assertEqual(
                    contract.operating_unit_id,
                    period.operating_unit_id,
                    "Draft contract in period has same OU as payroll period",
                )

    def test_register_payslips(self):

        start = datetime(2021, 9, 1)
        schedule = self.create_payroll_schedule("monthly", start.date())
        schedule.use_operating_units = True
        cc1 = self.create_contract(
            self.employee_emp.id,
            "draft",
            "done",
            date(2021, 1, 1),
            pps_id=schedule.id,
            job_id=self.job_ux_designer.id,
        )
        cc2 = self.create_contract(
            self.employee_sally.id,
            "draft",
            "done",
            date(2021, 1, 1),
            pps_id=schedule.id,
            job_id=self.job_hradmin.id,
        )
        cc1.operating_unit_id = self.ou_main
        cc2.operating_unit_id = self.ou_second
        self.apply_contract_cron()
        schedule.add_pay_period()

        pp_main_ids = self.Period.with_user(self.payrollOfficer.id).search(
            [("operating_unit_id", "=", self.ou_main.id)]
        )
        pp_second_ids = self.Period.with_user(self.payrollOfficer.id).search(
            [("operating_unit_id", "=", self.ou_second.id)]
        )
        self.assertEqual(
            len(pp_main_ids), 1, "There is exactly one payroll period for Main OU"
        )
        self.assertEqual(
            len(pp_second_ids), 1, "There is exactly one payroll period for Second OU"
        )

        # Process Main payroll period wizard
        wiz = (
            self.Wizard.with_user(self.payrollOfficer)
            .with_context({"active_id": pp_main_ids[0].id})
            .create({})
        )
        wiz.create_payroll_register()
        pp_main_ids = self.Period.with_user(self.payrollOfficer.id).search(
            [("operating_unit_id", "=", self.ou_main.id)]
        )
        self.assertTrue(
            pp_main_ids.register_id, "The Main OU payroll period has a payroll sheet"
        )
        self.assertEqual(
            len(pp_main_ids.register_id.run_ids),
            1,
            "There is only one payslip batch in Main OU",
        )
        self.assertEqual(
            len(pp_main_ids.register_id.run_ids.slip_ids),
            1,
            "There is only one payslip in Main OU payslip batch",
        )
        self.assertEqual(
            pp_main_ids.register_id.run_ids.slip_ids.operating_unit_id,
            self.ou_main,
            "The one payslip has same OU as period",
        )

        # Process Second payroll period wizard
        wiz = (
            self.Wizard.with_user(self.payrollOfficer)
            .with_context({"active_id": pp_second_ids[0].id})
            .create({})
        )
        wiz.create_payroll_register()
        pp_second_ids = self.Period.with_user(self.payrollOfficer.id).search(
            [("operating_unit_id", "=", self.ou_second.id)]
        )
        self.assertTrue(
            pp_second_ids.register_id,
            "The Second OU payroll period has a payroll sheet",
        )
        self.assertEqual(
            len(pp_second_ids.register_id.run_ids),
            1,
            "There is only one payslip batch in Second OU",
        )
        self.assertEqual(
            len(pp_second_ids.register_id.run_ids.slip_ids),
            1,
            "There is only one payslip in Second OU payslip batch",
        )
        self.assertEqual(
            pp_second_ids.register_id.run_ids.slip_ids.operating_unit_id,
            self.ou_second,
            "The one payslip has same OU as period",
        )
