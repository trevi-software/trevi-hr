# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.fields import Date
from odoo.tests.common import TransactionCase


class TestHrCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # -- models
        # ``hr.contract`` was merged into ``hr`` and renamed to ``hr.version``.
        cls.Version = cls.env["hr.version"]
        cls.Department = cls.env["hr.department"]
        cls.Employee = cls.env["hr.employee"]
        cls.Job = cls.env["hr.job"]

        # departments
        cls.dept_sales = cls.Department.create({"name": "#Sales"})

        # Creating an employee already creates an ``hr.version`` dated today, and
        # ``hr.version`` enforces a unique ``(employee_id, date_version)`` index.
        # The version under test is therefore dated one day earlier; its effective
        # contract dates are still driven by ``contract_date_start``/``_end``.
        cls.version_data = {
            "name": "Contract #1",
            "employee_id": False,
            "job_id": False,
            "wage": 1,
            "date_version": Date.today() - timedelta(days=1),
            "contract_date_start": Date.today(),
            "contract_date_end": Date.today() + timedelta(days=90),
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
                "parent_id": parent_job.id if parent_job else False,
                "department_manager": is_manager,
                "department_id": department.id if department else False,
                "employee_ids": employees_xpr,
            }
        )

    def create_version(self, name, employee, job=None, start_date=None, end_date=None):
        v_data = self.version_data.copy()
        v_data.update(
            {
                "name": name if name else v_data["name"],
                "employee_id": employee.id,
                "job_id": job.id if job else False,
            }
        )
        return self.Version.create(v_data)

    def create_version_multi(self, versions):
        return self.Version.create(versions)
