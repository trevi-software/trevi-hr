# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import common


class TestContractInit(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.HrEmployee = cls.env["hr.employee"]
        # Odoo 19 merged ``hr_contract`` into ``hr``: ``hr.contract`` is now
        # ``hr.version`` and it is what carries the contract (wage, job,
        # trial period, ...) data.
        cls.HrVersion = cls.env["hr.version"]
        cls.HrJob = cls.env["hr.job"]
        cls.HrCategory = cls.env["hr.employee.category"]
        cls.HrContractInit = cls.env["hr.contract.init"]

        # -- Categories
        cls.category_it = cls.HrCategory.create({"name": "#IT", "employee_ids": False})
        cls.category_marketing = cls.HrCategory.create(
            {"name": "#Marketing", "employee_ids": False}
        )

        # -- Jobs
        # hr_contract_status makes hr.job.department_id required
        cls.department = cls.env["hr.department"].create({"name": "#Test Dept"})
        cls.job_mkt_director = cls.HrJob.create(
            {
                "name": "#Marketing Director",
                "category_ids": [(4, cls.category_marketing.id)],
                "department_id": cls.department.id,
            }
        )
        cls.job_ux_designer = cls.HrJob.create(
            {
                "name": "#UX Designer",
                "category_ids": [(4, cls.category_it.id)],
                "department_id": cls.department.id,
            }
        )

        # The employee always owns one version, so it is backdated to leave
        # today's effective date free for the versions created by the tests.
        cls.eeJohn = cls.HrEmployee.create(
            {"name": "John", "date_version": "2000-01-01"}
        )

    def _create_contract(self, vals=None):
        values = {
            "name": "C1",
            "employee_id": self.eeJohn.id,
        }
        values.update(vals or {})
        return self.HrVersion.create(values)

    def test_load_latest_values(self):
        """Initial values are loaded from the latest values"""

        countInits = self.HrContractInit.search_count([])

        # Create two init values
        self.HrContractInit.create(
            {
                "name": "Way in the past",
                "date": "2000-01-01",
                "trial_period": 45,
            }
        )
        rightInit = self.HrContractInit.create(
            {
                "name": "Today",
                "date": fields.Date.today(),
                "trial_period": 60,
            }
        )

        contract = self._create_contract({"wage": 1.0})
        delta = (contract.trial_date_end - contract.trial_date_start).days
        cInits = self.HrContractInit.search([])
        self.assertEqual(countInits + 2, len(cInits))
        self.assertEqual(delta, rightInit.trial_period)

    def test_delete_locked(self):
        """Unlinking locked record raises an error"""

        cInit = self.HrContractInit.create(
            {
                "name": "Way in the past",
                "date": "2000-01-01",
                "trial_period": 45,
            }
        )
        cInit.lock()
        with self.assertRaises(UserError):
            cInit.unlink()

    def test_write_locked(self):
        """Updating a locked record raises a UserError"""

        cInit = self.HrContractInit.create(
            {
                "name": "Way in the past",
                "date": "2000-01-01",
                "trial_period": 45,
            }
        )
        cInit.lock()
        with self.assertRaises(UserError):
            cInit.trial_period = 100

    def test_lock_then_unlock(self):
        """Lock a record then unlock it and write to it"""

        cInit = self.HrContractInit.create(
            {
                "name": "Way in the past",
                "date": "2000-01-01",
                "trial_period": 45,
            }
        )
        cInit.lock()
        with self.assertRaises(UserError):
            cInit.trial_period = 100
        cInit.unlock()
        try:
            cInit.trial_period = 80
        except UserError:
            self.fail("An unexpected UserError exception was raised!")

    def test_get_wage_default(self):
        """Creating a contract with a default initial value succeeds"""

        self.HrContractInit.create(
            {
                "name": "Today",
                "date": fields.Date.today(),
                "trial_period": 60,
                "wage_ids": [(0, 0, {"starting_wage": 1000, "is_default": True})],
            }
        )
        contract = self._create_contract()
        self.assertEqual(1000, contract.wage)

    def test_get_wage_by_job_id(self):
        """Creating a contract with a job that has an applicable
        initial value succeeds"""

        self.HrContractInit.create(
            {
                "name": "Today",
                "date": fields.Date.today(),
                "trial_period": 60,
                "wage_ids": [
                    (
                        0,
                        0,
                        {
                            "job_id": self.job_mkt_director.id,
                            "starting_wage": 1000,
                            "is_default": True,
                        },
                    ),
                    (0, 0, {"job_id": self.job_ux_designer.id, "starting_wage": 2000}),
                ],
            }
        )
        contract = self._create_contract({"job_id": self.job_ux_designer.id})
        self.assertEqual(2000, contract.wage)

    def test_get_wage_by_category(self):
        """Creating a contract with a job category that has an
        applicable initial value succeeds"""

        self.HrContractInit.create(
            {
                "name": "Today",
                "date": fields.Date.today(),
                "trial_period": 60,
                "wage_ids": [
                    (
                        0,
                        0,
                        {
                            "job_id": self.job_mkt_director.id,
                            "starting_wage": 1000,
                            "is_default": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "starting_wage": 2000,
                            "category_ids": [(4, self.category_it.id)],
                        },
                    ),
                ],
            }
        )
        contract = self._create_contract({"job_id": self.job_ux_designer.id})
        self.assertEqual(2000, contract.wage)

    def test_get_latest_values_follow_the_environment_company(self):
        """Initial values come from the company the caller works in.

        ``get_latest_initial_values`` searches with ``sudo()``, so the company
        must come from the environment - ``with_company()``, which Odoo refuses
        for a company the user may not access - and never from caller-supplied
        context: otherwise another company's initial values (default starting
        wage, trial period, ...) would flow into the caller's contract version.
        """

        own_company = self.env.company
        other_company = self.env["res.company"].create({"name": "#Other Company"})

        own_init = self.HrContractInit.create(
            {
                "name": "#Own initial values",
                "date": fields.Date.today(),
                "company_id": own_company.id,
                "wage_ids": [(0, 0, {"starting_wage": 1111, "is_default": True})],
            }
        )
        other_init = self.HrContractInit.create(
            {
                "name": "#Other initial values",
                "date": fields.Date.today(),
                "company_id": other_company.id,
                "wage_ids": [(0, 0, {"starting_wage": 9999, "is_default": True})],
            }
        )

        # the values follow the company in the environment
        self.assertEqual(
            own_init,
            self.HrVersion.with_company(own_company).get_latest_initial_values(),
        )
        self.assertEqual(
            other_init,
            self.HrVersion.with_company(other_company).get_latest_initial_values(),
        )

        # a user restricted to their own company cannot reach the other one's
        # values: Odoo either refuses the company or the search stays local
        user = self.env["res.users"].create(
            {
                "name": "#Limited HR User",
                "login": "#limited_hr_user",
                "company_id": own_company.id,
                "company_ids": [(6, 0, [own_company.id])],
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("hr.group_hr_user").id,
                        ],
                    )
                ],
            }
        )

        try:
            leaked = (
                self.HrVersion.with_user(user)
                .with_company(other_company)
                .get_latest_initial_values()
            )
        except AccessError:
            leaked = own_init
        self.assertEqual(own_init, leaked)
