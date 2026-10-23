# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common


class TestEmployeeContract(common.TransactionCase):
    """The employee side of a contract version."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrVersion = cls.env["hr.version"]
        cls.Job = cls.env["hr.job"]
        cls.Dept = cls.env["hr.department"]

        cls.dept_rnd = cls.Dept.create({"name": "R&D"})
        cls.job_ux_designer = cls.Job.create(
            {"name": "#UX Designer", "department_id": cls.dept_rnd.id}
        )

    def create_employee(self, name="John", **vals):
        return self.HrEmployee.create(dict({"name": name}, **vals))

    def test_new_contract_sets_job_and_department(self):
        """The employee's job and department follow its contract version"""

        employee = self.create_employee()
        self.assertFalse(employee.job_id)
        self.assertFalse(employee.department_id)

        contract = employee.version_id
        contract.job_id = self.job_ux_designer

        self.assertEqual(self.job_ux_designer, employee.job_id)
        self.assertEqual(self.dept_rnd, employee.department_id)

    def test_version_native_flags(self):
        """A running/finished contract is described by the native flags"""

        today = fields.Date.today()
        employee = self.create_employee()
        contract = employee.version_id
        contract.write(
            {
                "contract_date_start": today + relativedelta(days=-10),
                "contract_date_end": today + relativedelta(days=10),
            }
        )

        self.assertTrue(contract.is_current)
        self.assertFalse(contract.is_past)
        self.assertFalse(contract.is_future)

        contract.contract_date_end = today + relativedelta(days=-1)
        # hr.version.write() re-synchronizes the contract dates through a
        # nested write, which leaves the (non stored) date flags cached with
        # their previous value; clear the cache before reading them.
        self.env.invalidate_all()
        self.assertTrue(contract.is_past)
        self.assertFalse(contract.is_current)

    def test_consecutive_contracts(self):
        """_get_contracts() lists every contract of the period, ended or not"""

        employee = self.create_employee("Jane", date_version="2021-01-01")
        ended = employee.version_id
        ended.write(
            {
                "contract_date_start": date(2021, 1, 1),
                "contract_date_end": date(2021, 1, 14),
            }
        )
        running = self.HrVersion.create(
            {
                "name": "Contract 2",
                "employee_id": employee.id,
                "wage": 1,
                "date_version": date(2021, 1, 15),
                "contract_date_start": date(2021, 1, 15),
            }
        )

        contracts = employee._get_contracts(date(2021, 1, 1), date(2021, 1, 31))[
            employee.id
        ]

        self.assertIn(ended, contracts, "The ended contract is in the period")
        self.assertIn(running, contracts, "The running contract is in the period")

    def test_get_trial_contract(self):
        """_get_contracts() returns the contract of a trial period"""

        today = date.today()
        employee = self.create_employee("Jane")
        contract = employee.version_id
        contract.write(
            {
                "contract_date_start": today,
                "trial_date_end": today + relativedelta(days=30),
            }
        )

        self.assertEqual(contract.trial_date_end, today + relativedelta(days=30))

        contracts = employee._get_contracts(
            date_start=today, date_end=today + relativedelta(days=30)
        )[employee.id]

        self.assertIn(contract, contracts, "The trial contract is in the period")
