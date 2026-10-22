# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import common


class TestEmployeeStatus(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.Employee = cls.env["hr.employee"]

    def create_employee(self, name="John Smith"):
        return self.Employee.create({"name": name})

    def create_contract(self, employee, start, end=None, trial_end=None):
        """Set the dates of the employee's version (their contract)."""
        version = employee.version_id or employee.version_ids[:1]
        version.write(
            {
                "contract_date_start": start,
                "contract_date_end": end,
                "trial_date_end": trial_end,
                "wage": 1,
            }
        )
        return version

    def update_status(self):
        """Run the status update the module's cron calls."""
        self.env["hr.version"].update_employee_status()

    def run_cron(self, xmlid):
        """Run the action a cron job schedules, in the current transaction.

        Odoo 19 runs ``ir.cron.method_direct_trigger`` in a transaction of its
        own, so its changes are invisible to the test; running the action the
        cron executes is the same code path.
        """
        self.env.ref(xmlid).ir_actions_server_id.run()

    def test_new_employee_state(self):
        """New employee status is 'new'"""

        ee = self.create_employee()
        self.assertEqual("new", ee.status)

    def test_contract_with_trial_period(self):
        """A running contract with a trial period puts the employee on trial"""

        start = date.today() - relativedelta(days=100)
        trial_end = date.today() + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, trial_end=trial_end)
        self.assertEqual("new", ee.status)

        self.update_status()
        self.assertEqual("trial", ee.status)
        self.assertTrue(cc.is_in_contract)

    def test_contract_without_trial_period(self):
        """A running contract without trial period makes the employee active"""

        start = date.today() - relativedelta(days=100)
        ee = self.create_employee()
        cc = self.create_contract(ee, start)
        self.assertEqual("new", ee.status)

        self.update_status()
        self.assertEqual("active", ee.status)
        self.assertTrue(cc.is_in_contract)

    def test_future_contract_does_not_change_status(self):
        """A contract that has not started yet does not change the status"""

        start = date.today() + relativedelta(days=10)
        ee = self.create_employee()
        cc = self.create_contract(ee, start)

        self.update_status()
        self.assertEqual("new", ee.status)
        self.assertTrue(cc.is_future)

    def test_trial_to_active(self):
        """When the trial period is over the employee becomes active"""

        start = date.today() - relativedelta(days=100)
        trial_end = date.today() + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, trial_end=trial_end)

        self.update_status()
        self.assertEqual("trial", ee.status)

        # End trial
        cc.trial_date_end = date.today() - relativedelta(days=1)
        self.update_status()
        self.assertEqual("active", ee.status)

    def test_status_update_cron(self):
        """The status update is wired as a cron job"""

        start = date.today() - relativedelta(days=100)
        ee = self.create_employee()
        self.create_contract(ee, start)

        self.run_cron("hr_employee_status.ir_cron_data_hr_version_update_status")
        self.assertEqual("active", ee.status)

    def test_premature_transition_to_active(self):
        """Transition from trial to active before trial period ends is prohibited"""

        start = date.today() - relativedelta(days=100)
        trial_end = date.today() + relativedelta(days=60)
        ee = self.create_employee()
        self.create_contract(ee, start, trial_end=trial_end)

        self.update_status()
        self.assertEqual("trial", ee.status)

        with self.assertRaises(UserError):
            ee.status = "active"

    def test_reactivate_employee(self):
        """Re-activating an inactive employee re-opens an ended contract"""

        start = date.today() - relativedelta(days=100)
        end = date.today() - relativedelta(days=1)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)

        ee.set_state_inactive()
        self.assertEqual("inactive", ee.status)
        self.assertFalse(ee.active)

        ee.signal_reactivate()
        self.assertEqual("active", ee.status)
        self.assertTrue(ee.active)
        self.assertFalse(cc.contract_date_end)
        self.assertTrue(cc.is_in_contract)
