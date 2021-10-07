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
        cls.Separation = cls.env["hr.employee.termination"]
        cls.reason = cls.env["hr.employee.termination.reason"].create(
            {"name": "Retired"}
        )

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

    def apply_separation_cron(self):
        self.env.ref(
            "hr_employee_status.ir_cron_data_separation_update_state"
        ).method_direct_trigger()

    def create_contract(
        self, employee, state, kanban_state, start, end=None, trial_end=None
    ):
        return self.Contract.create(
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

    def create_separation(self, employee, date=None):
        if date is None:
            date = date.today()
        return self.Separation.create(
            {
                "name": date,
                "reason_id": self.reason.id,
                "employee_id": employee.id,
            }
        )

    def test_separation_triggers_status_change(self):
        """Employee separation changes employee/contract -> pending_separation"""

        start = date.today() - relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual("open", cc.state)
        self.assertEqual(sep_date, cc.date_end)
        self.assertFalse(sep.contract_date_end)

    def test_cancel_separation_trial(self):
        """Cancelling of separation of employee in trial period reverts
        contract and employee back to trial"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        trial_end = date.today() + relativedelta(days=50)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end, trial_end)
        cc.signal_confirm()
        self.assertEqual("trial", cc.state)
        self.assertEqual("trial", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual("trial", cc.state)
        self.assertEqual(sep_date, cc.date_end)
        self.assertEqual(end, sep.contract_date_end)

        # cancel separation
        sep.signal_cancel()
        self.assertEqual("trial", cc.state)
        self.assertEqual("trial", ee.status)
        self.assertEqual("cancel", sep.state)

    def test_cancel_separation_open(self):
        """Cancelling of sepration of employee with active status reverts
        contract and employee back to open/active"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual("open", cc.state)
        self.assertEqual(sep_date, cc.date_end)
        self.assertEqual(end, sep.contract_date_end)

        # cancel separation
        sep.signal_cancel()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual("cancel", sep.state)

    def test_unlink_separation_trial(self):
        """Unlinking of separation of employee in trial period reverts
        contract and employee back to trial"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        trial_end = date.today() + relativedelta(days=50)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end, trial_end)
        cc.signal_confirm()
        self.assertEqual("trial", cc.state)
        self.assertEqual("trial", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual("trial", cc.state)
        self.assertEqual(sep_date, cc.date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Unlink() separation
        sep.unlink()
        self.assertEqual("trial", cc.state)
        self.assertEqual("trial", ee.status)

    def test_unlink_separation_open(self):
        """Unlinking of sepration of employee with active status reverts
        contract and employee back to open/active"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual("open", cc.state)
        self.assertEqual(sep_date, cc.date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Unlink() separation
        sep.unlink()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)
        self.assertTrue(ee.active)

    def test_autoconfirm_separation(self):
        """When separation date arrives, cron changes the status of
        separation, employee, and contract"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual("open", cc.state)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Update separation date to yesterday and run cron
        sep.name = date.today() - relativedelta(days=1)
        self.apply_separation_cron()

        self.assertEqual("done", sep.state)
        self.assertEqual("inactive", ee.status)
        self.assertFalse(ee.active)
        self.assertEqual("close", cc.state)
        self.assertEqual("done", sep.state)

    def test_done_separation(self):
        """When user clicks the 'done' button it changes the status of
        separation, employee, and contract"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual("open", cc.state)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Update separation date to today and set done
        sep.name = date.today()
        sep.signal_done()

        self.assertEqual("done", sep.state)
        self.assertEqual("inactive", ee.status)
        self.assertFalse(ee.active)
        self.assertEqual("close", cc.state)
        self.assertEqual("done", sep.state)

    def test_done_separation_archives_all(self):
        """When the separation is done employee and contracts should be archived"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual("open", cc.state)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.date_end)
        self.assertEqual(end, sep.contract_date_end)

        # Update separation date to today and set done
        sep.name = date.today()
        sep.signal_done()

        self.assertFalse(ee.active)
        self.assertFalse(cc.active)

    def test_done_separation_in_future(self):
        """When user clicks the 'done' button before the separation date
        it refuses"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # Create separation
        sep = self.create_separation(ee, sep_date)
        self.assertEqual("draft", sep.state)
        self.assertEqual("separation", ee.status)
        self.assertEqual("open", cc.state)
        self.assertTrue(ee.active)
        self.assertEqual(sep_date, cc.date_end)
        self.assertEqual(end, sep.contract_date_end)

        with self.assertRaises(UserError):
            sep.signal_done()
