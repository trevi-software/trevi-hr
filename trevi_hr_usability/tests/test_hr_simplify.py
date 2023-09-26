# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.fields import Date
from odoo.tests.common import Form, SavepointCase


class TestHrSimplify(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestHrSimplify, cls).setUpClass()

        # -- models
        cls.Contract = cls.env["hr.contract"]
        cls.Department = cls.env["hr.department"]
        cls.Employee = cls.env["hr.employee"]
        cls.Job = cls.env["hr.job"]

        # -- departments
        cls.dept_marketing = cls.Department.create({"name": "Marketing"})
        cls.dept_RandD = cls.Department.create({"name": "Research and Development"})

        # -- jobs
        # -- marketing
        cls.job_mkt_director = cls.Job.create({"name": "Marketing Director"})

        # -- R&D
        cls.job_rnd_manager = cls.Job.create(
            {
                "name": "Research and Development Manager",
                "no_of_recruitment": 2,
            }
        )
        cls.job_rnd_technician = cls.Job.create(
            {
                "name": "Research and Development Technician",
                "no_of_recruitment": 4,
            }
        )

        # -- employees
        cls.emp_adam = cls.Employee.create(
            {
                "name": "Adam",
                "gender": "male",
                "department_id": cls.dept_marketing.id,
                "job_id": cls.job_mkt_director.id,
                "active": True,
            }
        )

        cls.emp_kal = cls.Employee.create(
            {
                "name": "Kal",
                "gender": "female",
                "department_id": cls.dept_RandD.id,
                "job_id": cls.job_rnd_manager.id,
                "active": True,
            }
        )

        cls.emp_tim = cls.Employee.create(
            {
                "name": "Tim",
                "gender": "male",
                "department_id": cls.dept_RandD.id,
                "job_id": cls.job_rnd_technician.id,
                "active": True,
            }
        )

        cls.emp_ed = cls.Employee.create(
            {
                "name": "Ed",
                "gender": "male",
                "department_id": cls.dept_RandD.id,
                "job_id": cls.job_rnd_technician.id,
                "active": True,
            }
        )

        # -- contract data
        cls.contract_data = {
            "state": "open",
            "kanban_state": "normal",
            "wage": 1,
            "date_start": False,
            "date_end": False,
        }

    def create_contract(
        self, employee, job, start_date=None, end_date=None, name="Contract#1"
    ):
        self.contract_data["name"] = name
        self.contract_data["employee_id"] = employee.id
        self.contract_data["job_id"] = job.id
        self.contract_data["date_start"] = (
            Date.today() if start_date is None else start_date
        )
        self.contract_data["date_end"] = (
            Date.today() + timedelta(days=90) if end_date is None else end_date
        )
        return self.Contract.create(self.contract_data)

    def test_employee_country_defaults_to_et(self):
        self.assertEqual(self.emp_adam.country_id, self.env.ref("base.et"))
        self.assertEqual(self.emp_kal.country_id, self.env.ref("base.et"))

    def test_onchange_employee_id(self):
        contract = self.create_contract(self.emp_adam, self.job_mkt_director)
        with Form(contract) as f:
            f.employee_id = self.emp_kal
            f.job_id = self.job_mkt_director
            if self.env.ref("payroll.structure_base"):
                f.struct_id = self.env.ref("payroll.structure_base")
            self.assertEqual(f.employee_dept_id, self.dept_RandD)

    def test_compute_employees(self):
        self.create_contract(
            name="Kal Contract",
            employee=self.emp_kal,
            job=self.job_rnd_manager,
            start_date=(Date.today() - timedelta(days=(5 * 30))),
            end_date=(Date.today() - timedelta(days=(2 * 30))),
        )
        self.create_contract(
            name="Tim Contract",
            employee=self.emp_tim,
            job=self.job_rnd_technician,
            start_date=(Date.today() - timedelta(days=(6 * 30))),
            end_date=(Date.today() - timedelta(days=(2 * 30))),
        )
        self.create_contract(
            name="Ed Contract",
            employee=self.emp_ed,
            job=self.job_rnd_technician,
            start_date=(Date.today() - timedelta(days=(4 * 30))),
            end_date=(Date.today() - timedelta(days=30)),
        )

        self.assertEqual(self.job_rnd_manager.no_of_employee, 1)
        self.assertEqual(
            self.job_rnd_manager.expected_employees,
            (self.job_rnd_manager.no_of_recruitment + 1),
        )

        self.assertEqual(self.job_rnd_technician.no_of_employee, 2)
        self.assertEqual(
            self.job_rnd_technician.expected_employees,
            (self.job_rnd_technician.no_of_recruitment + 2),
        )
