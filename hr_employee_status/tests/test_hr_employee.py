# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import common


class TestEmployee(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestEmployee, cls).setUpClass()

        cls.Employee = cls.env["hr.employee"]
        cls.Contract = cls.env["hr.contract"]

    def create_employee(self, name="John Smith"):
        return self.Employee.create(
            {
                "name": name,
            }
        )

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def create_contract(
        self, employee, state, kanban_state, start, end=None, trial_end=None
    ):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": employee.id,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
            }
        )

    def test_new_employee_state(self):
        """New employee status is 'new'"""

        ee = self.create_employee()
        self.assertEqual("new", ee.status)

    def test_contract_open_trigger(self):
        """When contract changes to open new employee should go to trial period"""

        start = date.today()
        end = start + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "normal", start, trial_end=end)
        self.assertEqual("new", ee.status)

        # Open contract
        cc.signal_confirm()
        self.assertEqual("trial", cc.state)
        self.assertEqual("trial", ee.status)

    def test_contract_autoopen_trigger(self):
        """When contract auto-updates to open new employee should go to trial period"""

        start = date.today()
        end = start + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, trial_end=end)
        self.assertEqual("new", ee.status)

        # Open contract
        self.apply_contract_cron()
        self.assertEqual("trial", cc.state)
        self.assertEqual("trial", ee.status)

    def test_contract_open_notrigger_trial(self):
        """A contract without trial period does not trigger employee trial period"""

        start = date.today()
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "normal", start)
        self.assertEqual("new", ee.status)

        # Open contract
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

    def test_contract_autoopen_notrigger_trial(self):
        """When A contract without trial period auto-updates to 'running' it
        does not trigger employee trial period"""

        start = date.today()
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start)
        self.assertEqual("new", ee.status)

        # Open contract
        self.apply_contract_cron()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

    def test_trial_to_active(self):
        """When the contract goes 'open' employee should move trial->active"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "normal", start, trial_end=end)
        self.assertEqual("new", ee.status)

        # Open contract
        cc.signal_confirm()
        self.assertEqual("trial", cc.state)
        self.assertEqual("trial", ee.status)

        # End trial
        cc.trial_date_end = date.today() - relativedelta(days=1)
        self.apply_contract_cron()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

    def test_premature_transition_to_active(self):
        """Transition from trial to active before trial period ends is prohibited"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "normal", start, trial_end=end)
        self.assertEqual("new", ee.status)

        # Open contract
        cc.signal_confirm()
        self.assertEqual("trial", cc.state)
        self.assertEqual("trial", ee.status)

        with self.assertRaises(UserError):
            ee.status = "active"
