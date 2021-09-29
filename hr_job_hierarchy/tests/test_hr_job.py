# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .common import TestHrCommon


class TestHrJob(TestHrCommon):
    @classmethod
    def setUpClass(cls):
        super(TestHrJob, cls).setUpClass()

    def test_employee_with_manager_job_position_is_set_as_department_manager(self):
        emp_SM = self.create_employee("#EMP (sale manager)")
        job_SM = self.create_job(
            "#Sales Manager", department=self.dept_sales, employees=emp_SM
        )
        job_SM.department_manager = True
        self.assertEqual(self.dept_sales.manager_id, emp_SM)

    def test_parent_job_position_employee_is_set_as_employee_parent(self):
        emp_SM = self.create_employee("#EMP (sales manager)")
        emp_SA = self.create_employee("#EMP (sales associate)")
        job_SM = self.create_job(
            name="#Sales Manager",
            department=self.dept_sales,
            is_manager=True,
            employees=emp_SM,
        )
        job_SA = self.create_job(
            name="#Sales Associate",
            parent_job=job_SM,
            department=self.dept_sales,
            employees=emp_SA,
        )
        job_SA.parent_id = job_SM
        self.assertEqual(emp_SA.parent_id, emp_SM)
