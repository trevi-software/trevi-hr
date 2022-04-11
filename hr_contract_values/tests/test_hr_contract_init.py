# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestContractInit(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestContractInit, cls).setUpClass()

        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.HrJob = cls.env["hr.job"]
        cls.HrCategory = cls.env["hr.employee.category"]
        cls.HrContractInit = cls.env["hr.contract.init"]

        # -- Categories
        cls.category_it = cls.HrCategory.create({"name": "#IT", "employee_ids": False})
        cls.category_marketing = cls.HrCategory.create(
            {"name": "#Marketing", "employee_ids": False}
        )

        # -- Jobs
        cls.job_mkt_director = cls.HrJob.create(
            {
                "name": "#Marketing Director",
                "category_ids": [(4, cls.category_marketing.id)],
            }
        )
        cls.job_ux_designer = cls.HrJob.create(
            {
                "name": "#UX Designer",
                "category_ids": [(4, cls.category_it.id)],
            }
        )

        cls.eeJohn = cls.HrEmployee.create({"name": "John"})

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

        contract = self.HrContract.create(
            {
                "name": "C1",
                "employee_id": self.eeJohn.id,
                "wage": 1.0,
            }
        )
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
        contract = self.HrContract.create(
            {
                "name": "C1",
                "employee_id": self.eeJohn.id,
            }
        )
        self.assertEqual(1000, contract.wage)

    def test_get_wage_by_job_id(self):
        """Creating a contract with a job that has an applicable initial value succeeds"""

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
        contract = self.HrContract.create(
            {
                "name": "C1",
                "employee_id": self.eeJohn.id,
                "job_id": self.job_ux_designer.id,
            }
        )
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
        contract = self.HrContract.create(
            {
                "name": "C1",
                "employee_id": self.eeJohn.id,
                "job_id": self.job_ux_designer.id,
            }
        )
        self.assertEqual(2000, contract.wage)
