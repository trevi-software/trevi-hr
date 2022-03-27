# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .common import TestHrCommon


class TestHrDepartment(TestHrCommon):
    @classmethod
    def setUpClass(cls):
        super(TestHrDepartment, cls).setUpClass()

    def test_department_manager_is_set_as_employees_manager(self):
        emp_SM = self.create_employee("#EMP (sales manager)")
        emp_SA = self.create_employee(
            "#EMP (sales associate)", department=self.dept_sales
        )
        emp_SR = self.create_employee(
            "#EMP (sales representative)", department=self.dept_sales
        )
        self.dept_sales.manager_id = emp_SM
        self.assertEqual(emp_SA.parent_id, emp_SM)
        self.assertEqual(emp_SR.parent_id, emp_SM)
