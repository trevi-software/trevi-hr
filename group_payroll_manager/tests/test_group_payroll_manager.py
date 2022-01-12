# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestGroupPayrollManager(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestGroupPayrollManager, cls).setUpClass()

        cls.ResPartner = cls.env["res.partner"]
        cls.ResUsers = cls.env["res.users"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.HrJob = cls.env["hr.job"]

        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="hel",
            groups="base.group_user,group_payroll_manager.group_payroll_manager",
            name="Simple employee",
            email="ric@example.com",
        )

    def test_hr_employee_read(self):
        """Has read access to hr.employee"""

        ee = self.HrEmployee.create({"name": "A"})
        try:
            ee.with_user(self.userPM.id).read(["name"])
        except AccessError:
            self.fail("raised an AccessError Exception")

    def test_hr_employee_write_fails(self):
        """Write access fails"""

        ee = self.HrEmployee.create({"name": "A"})
        with self.assertRaises(AccessError):
            ee.with_user(self.userPM.id).name = "B"

    def test_hr_employee_create_fails(self):
        """Create access fails"""

        with self.assertRaises(AccessError):
            self.HrEmployee.with_user(self.userPM.id).create({"name": "A"})

    def test_hr_employee_unlink_fails(self):
        """Unlink access fails"""

        ee = self.HrEmployee.create({"name": "A"})
        with self.assertRaises(AccessError):
            ee.with_user(self.userPM.id).unlink()

    def test_hr_contract_read(self):
        """Has read access to hr.contract"""

        ee = self.HrEmployee.create({"name": "A"})
        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": ee.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        try:
            contract.with_user(self.userPM.id).read([])
        except AccessError:
            self.fail("raised an AccessError Exception")

    def test_hr_contract_write_fails(self):
        """Write access fails"""

        ee = self.HrEmployee.create({"name": "A"})
        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": ee.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        with self.assertRaises(AccessError):
            contract.with_user(self.userPM.id).wage = 2

    def test_hr_contract_create_fails(self):
        """Create access fails"""

        ee = self.HrEmployee.create({"name": "A"})
        with self.assertRaises(AccessError):
            self.HrContract.with_user(self.userPM.id).create(
                {
                    "name": "CRef",
                    "employee_id": ee.id,
                    "date_start": fields.Date.today(),
                    "wage": 1,
                }
            )

    def test_hr_contract_unlink_fails(self):
        """Unlink access fails"""

        ee = self.HrEmployee.create({"name": "A"})
        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": ee.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        with self.assertRaises(AccessError):
            contract.with_user(self.userPM.id).unlink()

    def test_hr_job_read(self):
        """Has read access to hr.job"""

        job = self.HrJob.create({"name": "Job1"})
        try:
            job.with_user(self.userPM.id).read([])
        except AccessError:
            self.fail("raised an AccessError Exception")

    def test_hr_job_write_fails(self):
        """Write access fails"""

        job = self.HrEmployee.create({"name": "Job1"})
        with self.assertRaises(AccessError):
            job.with_user(self.userPM.id).name = "JOb2"

    def test_hr_job_create_fails(self):
        """Create access fails"""

        with self.assertRaises(AccessError):
            self.HrJob.with_user(self.userPM.id).create({"name": "Job1"})

    def test_hr_job_unlink_fails(self):
        """Unlink access fails"""

        job = self.HrJob.create({"name": "Job1"})
        with self.assertRaises(AccessError):
            job.with_user(self.userPM.id).unlink()
