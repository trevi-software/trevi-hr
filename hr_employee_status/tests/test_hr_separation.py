# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import common


class TestEmployeeSeparation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.Employee = cls.env["hr.employee"]
        cls.Separation = cls.env["hr.employee.termination"]
        cls.reason = cls.env["hr.employee.termination.reason"].create(
            {"name": "Retired"}
        )

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

    def apply_separation_cron(self):
        # Odoo 19 runs ``method_direct_trigger`` in its own transaction, whose
        # changes the test cannot see, so run the action the cron schedules.
        self.env.ref(
            "hr_employee_status.ir_cron_data_separation_update_state"
        ).ir_actions_server_id.run()

    def create_separation(self, employee, effective_date=None):
        if effective_date is None:
            effective_date = date.today()
        return self.Separation.create(
            {
                "name": effective_date,
                "reason_id": self.reason.id,
                "employee_id": employee.id,
            }
        )

    def test_separation_triggers_status_change(self):
        """Employee separation changes employee -> pending_separation and
        ends the contract on the separation's effective date"""

        start = date.today() - relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start)
        self.update_status()
        self.assertEqual("active", ee.status)
        self.assertTrue(cc.is_in_contract)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.contract_date_end)
        self.assertFalse(sep.contract_date_end)

    def test_cancel_separation_trial(self):
        """Cancelling of separation of employee in trial period reverts
        contract and employee back to trial"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        trial_end = date.today() + relativedelta(days=50)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end, trial_end)
        self.update_status()
        self.assertEqual("trial", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual(sep_date, cc.contract_date_end)
        self.assertEqual(end, sep.contract_date_end)

        # cancel separation
        sep.signal_cancel()
        self.assertEqual("trial", ee.status)
        self.assertEqual(end, cc.contract_date_end)
        self.assertTrue(cc.is_in_contract)
        self.assertEqual("cancel", sep.state)

    def test_cancel_separation_active(self):
        """Cancelling of separation of employee with active status reverts
        contract and employee back to active"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.update_status()
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.contract_date_end)
        self.assertEqual(end, sep.contract_date_end)

        # cancel separation
        sep.signal_cancel()
        self.assertEqual("active", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(end, cc.contract_date_end)
        self.assertTrue(cc.is_in_contract)
        self.assertEqual("cancel", sep.state)

    def test_unlink_separation_trial(self):
        """Unlinking of separation of employee in trial period reverts
        contract and employee back to trial"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        trial_end = date.today() + relativedelta(days=50)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end, trial_end)
        self.update_status()
        self.assertEqual("trial", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual(sep_date, cc.contract_date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Unlink() separation
        sep.unlink()
        self.assertEqual("trial", ee.status)
        self.assertEqual(end, cc.contract_date_end)
        self.assertTrue(cc.is_in_contract)

    def test_unlink_separation_active(self):
        """Unlinking of separation of employee with active status reverts
        contract and employee back to active"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.update_status()
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.contract_date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Unlink() separation
        sep.unlink()
        self.assertEqual("active", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(end, cc.contract_date_end)
        self.assertTrue(cc.is_in_contract)

    def test_autoconfirm_separation(self):
        """When the separation date arrives, the cron changes the status of
        the separation, the employee and the contract"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.update_status()
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.contract_date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Update separation date to yesterday and run cron
        sep.name = date.today() - relativedelta(days=1)
        self.apply_separation_cron()

        self.assertEqual("done", sep.state)
        self.assertEqual("inactive", ee.status)
        self.assertFalse(ee.active)
        self.assertEqual(date.today() - relativedelta(days=1), cc.contract_date_end)
        self.assertTrue(cc.is_past)

    def test_done_separation(self):
        """When the user clicks the 'done' button it changes the status of
        the separation, the employee and the contract"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.update_status()
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.contract_date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Update separation date to today and set done
        sep.name = date.today()
        sep.signal_done()

        self.assertEqual("done", sep.state)
        self.assertEqual("inactive", ee.status)
        self.assertFalse(ee.active)
        self.assertEqual(date.today(), cc.contract_date_end)

    def test_done_separation_archives_employee(self):
        """When the separation is done the employee is archived.

        The contract is ended, not archived: ``hr.version`` forbids archiving
        every version of an employee.
        """

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.update_status()
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)

        # Update separation date to today and set done
        sep.name = date.today()
        sep.signal_done()

        self.assertFalse(ee.active)
        self.assertEqual(date.today(), cc.contract_date_end)

    def test_unlink_done_separation(self):
        """A completed separation may not be deleted"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        self.create_contract(ee, start, end)
        self.update_status()
        self.assertEqual("active", ee.status)

        sep = self.create_separation(ee, sep_date)
        sep.name = date.today()
        sep.signal_done()
        self.assertEqual("done", sep.state)

        with self.assertRaises(UserError):
            sep.unlink()

    def test_done_separation_in_future(self):
        """When the user clicks the 'done' button before the separation date
        it refuses"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.update_status()
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.contract_date_end)
        self.assertEqual(end, sep.contract_date_end)

        with self.assertRaises(UserError):
            sep.signal_done()

    def test_ordinary_user_read_access(self):
        """Ordinary users only read their own (and subordinates') separations

        HR officers keep full access.
        """

        base_group_user = self.env.ref("base.group_user")
        hr_group_user = self.env.ref("hr.group_hr_user")

        plain_user = self.env["res.users"].create(
            {
                "name": "Plain Employee User",
                "login": "plain_employee_user",
                "group_ids": [(6, 0, [base_group_user.id])],
            }
        )
        hr_user = self.env["res.users"].create(
            {
                "name": "HR Officer User",
                "login": "hr_officer_user",
                "group_ids": [(6, 0, [base_group_user.id, hr_group_user.id])],
            }
        )

        own_ee = self.create_employee("Own Employee")
        self.create_contract(own_ee, date.today() - relativedelta(days=100))
        own_ee.user_id = plain_user
        other_ee = self.create_employee("Other Employee")
        self.create_contract(other_ee, date.today() - relativedelta(days=100))

        own_sep = self.create_separation(own_ee, date.today())
        other_sep = self.create_separation(other_ee, date.today())

        visible = self.Separation.with_user(plain_user).search([])
        self.assertIn(own_sep, visible)
        self.assertNotIn(other_sep, visible)

        visible_hr = self.Separation.with_user(hr_user).search([])
        self.assertIn(own_sep, visible_hr)
        self.assertIn(other_sep, visible_hr)
