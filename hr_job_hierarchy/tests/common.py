# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.fields import Date
from odoo.tests.common import SavepointCase


class TestHrCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestHrCommon, cls).setUpClass()

        # -- models
        cls.Contract = cls.env["hr.contract"]
        cls.Department = cls.env["hr.department"]
        cls.Employee = cls.env["hr.employee"]
        cls.Job = cls.env["hr.job"]

        # departments
        cls.dept_sales = cls.Department.create({"name": "#Sales"})

        cls.contract_data = {
            "name": "Contract #1",
            "employee_id": False,
            "job_id": False,
            "wage": 1,
            "state": "open",
            "kanban_state": "normal",
            "date_start": Date.today(),
            "date_end": Date.today() + timedelta(days=90),
        }

    def create_department(self, name):
        return self.Department.create({"name": name})

    def create_employee(self, name, department=None):
        return self.Employee.create(
            {"name": name, "department_id": department.id if department else False}
        )

    def create_job(
        self, name, parent_job=None, department=None, is_manager=False, employees=None
    ):
        employees_xpr = (
            [(4, employee.id) for employee in employees] if employees else False
        )
        return self.Job.create(
            {
                "name": name,
                "state": "open",
                "parent_id": parent_job.id if parent_job else False,
                "department_manager": is_manager,
                "department_id": department.id if department else False,
                "employee_ids": employees_xpr,
            }
        )

    def create_contract(self, name, employee, job=None, start_date=None, end_date=None):
        c_data = self.contract_data.copy()
        c_data.update(
            {
                "name": name if name else c_data["name"],
                "employee_id": employee.id,
                "job_id": job.id if job else False,
            }
        )
        return self.Contract.create(c_data)

    def create_contract_multi(self, contracts):
        return self.Contract.create(contracts)
