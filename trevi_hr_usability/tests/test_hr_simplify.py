# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests import Form, TransactionCase


class TestHrSimplify(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # -- models
        cls.Contract = cls.env["hr.version"]
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
        # Employees are created with a version dated in the past so that the
        # contract versions created by the tests do not clash with the
        # (employee_id, date_version) unique index of hr.version.
        cls.emp_adam = cls.Employee.create(
            {
                "name": "Adam",
                "sex": "male",
                "department_id": cls.dept_marketing.id,
                "job_id": cls.job_mkt_director.id,
                "active": True,
                "date_version": "2020-01-01",
            }
        )

        cls.emp_kal = cls.Employee.create(
            {
                "name": "Kal",
                "sex": "female",
                "department_id": cls.dept_RandD.id,
                "job_id": cls.job_rnd_manager.id,
                "active": True,
                "date_version": "2020-01-01",
            }
        )

        cls.emp_tim = cls.Employee.create(
            {
                "name": "Tim",
                "sex": "male",
                "department_id": cls.dept_RandD.id,
                "job_id": cls.job_rnd_technician.id,
                "active": True,
                "date_version": "2020-01-01",
            }
        )

        cls.emp_ed = cls.Employee.create(
            {
                "name": "Ed",
                "sex": "male",
                "department_id": cls.dept_RandD.id,
                "job_id": cls.job_rnd_technician.id,
                "active": True,
                "date_version": "2020-01-01",
            }
        )

    def create_contract(
        self, employee, job, start_date=None, end_date=None, name="Contract#1"
    ):
        start_date = Date.today() if start_date is None else start_date
        end_date = Date.today() + timedelta(days=90) if end_date is None else end_date
        return self.Contract.create(
            {
                "name": name,
                "employee_id": employee.id,
                "job_id": job.id,
                "wage": 1,
                "date_version": start_date,
                "contract_date_start": start_date,
                "contract_date_end": end_date,
            }
        )

    def test_employee_country_defaults_to_et(self):
        self.assertEqual(self.emp_adam.country_id, self.env.ref("base.et"))
        self.assertEqual(self.emp_kal.country_id, self.env.ref("base.et"))

    def test_onchange_employee_id(self):
        contract = self.create_contract(self.emp_adam, self.job_mkt_director)
        with Form(contract) as f:
            f.employee_id = self.emp_kal
            f.job_id = self.job_mkt_director
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

    def test_identification_unique_when_a_version_moves_to_another_employee(self):
        """Moving a version to another employee must not duplicate the number."""

        # one employee may carry the same official identification on several
        # versions of their own ...
        adam_v1 = self.create_contract(
            name="Adam #1",
            employee=self.emp_adam,
            job=self.job_mkt_director,
            start_date="2021-01-01",
            end_date="2021-12-31",
        )
        adam_v1.identification_id = "ET-12345"
        adam_v2 = self.create_contract(
            name="Adam #2",
            employee=self.emp_adam,
            job=self.job_mkt_director,
            start_date="2022-01-01",
            end_date=False,
        )
        adam_v2.identification_id = "ET-12345"

        # ... but moving one of them to somebody else would leave two employees
        # sharing the number
        with self.assertRaises(ValidationError):
            adam_v1.write({"employee_id": self.emp_kal.id})

    def test_compute_employees_counts_running_and_open_ended_versions(self):
        """An employee in post counts, whatever the end date of their version."""

        job = self.Job.create({"name": "Rolling Position"})

        def add_employee(name, start, end):
            return self.Employee.create(
                {
                    "name": name,
                    "department_id": self.dept_RandD.id,
                    "job_id": job.id,
                    "date_version": start,
                    "contract_date_start": start,
                    "contract_date_end": end,
                }
            )

        # an open-ended version
        add_employee("Open Ended", "2020-01-01", False)
        self.assertEqual(job.no_of_employee, 1)

        # a version still running, with an end date in the future
        add_employee(
            "Running",
            Date.today() - timedelta(days=30),
            Date.today() + timedelta(days=60),
        )
        self.assertEqual(job.no_of_employee, 2)

        # a version that has already ended
        add_employee("Ended", "2021-01-01", "2021-12-31")
        self.assertEqual(job.no_of_employee, 3)

    def test_compute_employees_counts_each_employee_once(self):
        """Historical and ended versions belong to the same employee."""

        job = self.Job.create({"name": "Historic Position"})
        employee = self.Employee.create(
            {
                "name": "Historic",
                "department_id": self.dept_RandD.id,
                "job_id": job.id,
                "date_version": "2020-01-01",
                "contract_date_start": "2020-01-01",
                "contract_date_end": "2020-06-30",
            }
        )
        # ended versions, with a day between them (hr.version forbids overlap)
        for nbr, (start, end) in enumerate(((400, 300), (250, 150)), start=1):
            self.create_contract(
                name=f"Historic #{nbr}",
                employee=employee,
                job=job,
                start_date=(Date.today() - timedelta(days=start)),
                end_date=(Date.today() - timedelta(days=end)),
            )
        # the current version is open-ended
        self.create_contract(
            name="Historic current",
            employee=employee,
            job=job,
            start_date=(Date.today() - timedelta(days=30)),
            end_date=False,
        )

        self.assertEqual(job.no_of_employee, 1)
        self.assertEqual(job.expected_employees, job.no_of_recruitment + 1)

    def test_compute_employees_ignores_superseded_versions(self):
        """A version replaced by a newer one no longer counts for its job."""

        junior = self.Job.create({"name": "Junior Technician"})
        senior = self.Job.create({"name": "Senior Technician"})
        employee = self.Employee.create(
            {
                "name": "Moved On",
                "department_id": self.dept_RandD.id,
                "job_id": junior.id,
                "date_version": "2020-01-01",
            }
        )
        self.create_contract(
            name="Moved On - junior",
            employee=employee,
            job=junior,
            start_date=(Date.today() - timedelta(days=300)),
            end_date=(Date.today() - timedelta(days=100)),
        )
        self.create_contract(
            name="Moved On - senior",
            employee=employee,
            job=senior,
            start_date=(Date.today() - timedelta(days=90)),
            end_date=(Date.today() + timedelta(days=200)),
        )

        self.assertEqual(senior.no_of_employee, 1)
        self.assertEqual(junior.no_of_employee, 0)
        self.assertEqual(junior.expected_employees, junior.no_of_recruitment)

        empty = self.Job.create({"name": "Nobody Here"})
        self.assertEqual(empty.no_of_employee, 0)
