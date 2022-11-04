# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestContract(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestContract, cls).setUpClass()

        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.employee = cls.HrEmployee.create({"name": "John"})
        cls.test_contract = dict(
            name="Test", wage=1, employee_id=cls.employee.id, state="draft"
        )

    def create_contract(self, state, kanban_state, start, end=None, trial_end=None):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": self.employee.id,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
            }
        )

    def apply_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def test_first_contract_open_notrial(self):
        """The first contract when 'Running' goes to
        'open' state, if trial end isn't set."""

        start = datetime.now().date()
        c = self.create_contract("draft", "normal", start)
        c.signal_confirm()
        self.assertEqual("open", c.state)
        self.assertEqual("normal", c.kanban_state)

    def test_first_contract_open_trial(self):
        """The first contract when 'Running' goes to
        trial period state, if trial end is set."""

        start = datetime.now().date()
        end = start + relativedelta(days=60)
        c = self.create_contract("draft", "normal", start, trial_end=end)
        c.signal_confirm()
        self.assertEqual("trial", c.state)
        self.assertEqual("normal", c.kanban_state)

    def test_next_contract_open_running(self):
        """Subsequent contracts go directly to 'Running' state"""

        start = datetime.strptime("2015-11-01", "%Y-%m-%d").date()
        end = datetime.strptime("2015-11-30", "%Y-%m-%d").date()
        self.create_contract("close", "normal", start, end)

        start = datetime.strptime("2015-12-01", "%Y-%m-%d").date()
        c2 = self.create_contract("draft", "normal", start)
        c2.signal_confirm()
        self.assertEqual("open", c2.state)
        self.assertEqual("normal", c2.kanban_state)

    def test_start_trial(self):
        """Cron update changes 'draft' contract into 'trial'"""

        self.test_contract.update(
            dict(
                trial_date_end=datetime.now() + relativedelta(days=100),
                kanban_state="done",
            )
        )
        contract = self.HrContract.create(self.test_contract)
        self.apply_cron()
        self.assertEqual("trial", contract.state)
        self.assertEqual("normal", contract.kanban_state)
        self.assertEqual(False, contract.trial_ending)
        self.assertEqual(False, self.employee.contract_warning)

    def test_trial_ending(self):
        self.test_contract.update(
            dict(trial_date_end=datetime.now() + relativedelta(days=100))
        )
        contract = self.HrContract.create(self.test_contract)
        contract.signal_confirm()
        self.assertEqual("trial", contract.state)
        self.assertEqual("normal", contract.kanban_state)
        self.assertEqual(False, contract.trial_ending)
        self.assertEqual(False, self.employee.contract_warning)

        self.test_contract.update(
            dict(trial_date_end=datetime.now() + relativedelta(days=5))
        )
        contract.write(self.test_contract)
        self.apply_cron()
        self.assertEqual(contract.state, "trial")
        self.assertEqual(contract.trial_ending, True)
        self.assertEqual(contract.kanban_state, "blocked")

    def test_trial_ended(self):
        self.test_contract.update(
            {
                "date_start": datetime.now() + relativedelta(days=-50),
                "trial_date_end": datetime.now() + relativedelta(days=100),
            }
        )
        contract = self.HrContract.create(self.test_contract)
        contract.signal_confirm()
        self.assertEqual("trial", contract.state)
        self.assertEqual("normal", contract.kanban_state)
        self.assertEqual(False, contract.trial_ending)
        self.assertEqual(False, self.employee.contract_warning)

        self.test_contract.update(
            {
                "trial_date_end": datetime.now() + relativedelta(days=-1),
            }
        )
        contract.write(self.test_contract)
        self.apply_cron()
        self.assertEqual("open", contract.state)
        self.assertEqual(False, contract.trial_ending)
        self.assertEqual("normal", contract.kanban_state)

    def test_contract_ending(self):
        """When a contract nears completion the relevant boolean should be set"""

        start = datetime.now().date()
        end = start + relativedelta(days=100)
        c = self.create_contract("draft", "normal", start, end)
        c.signal_confirm()
        self.assertEqual("open", c.state)
        self.assertEqual("normal", c.kanban_state)
        self.assertFalse(c.state_ending)

        c.date_end = start + relativedelta(days=5)
        self.apply_cron()
        self.assertEqual("open", c.state)
        self.assertEqual("blocked", c.kanban_state)
        self.assertTrue(c.state_ending)

    def test_contract_ended(self):
        """When a contract has ended the state should be 'close'"""

        # Start
        start = datetime.now().date() + relativedelta(days=-100)
        today = datetime.now().date()
        end = today + relativedelta(days=100)
        c = self.create_contract("draft", "normal", start, end)
        c.signal_confirm()
        self.assertEqual("open", c.state)
        self.assertEqual("normal", c.kanban_state)
        self.assertFalse(c.state_ending)

        # Ending
        c.date_end = today + relativedelta(days=5)
        self.apply_cron()
        self.assertEqual("open", c.state)
        self.assertEqual("blocked", c.kanban_state)
        self.assertTrue(c.state_ending)

        # Ended
        c.date_end = today + relativedelta(days=-1)
        self.apply_cron()
        self.assertEqual("close", c.state)
        self.assertEqual("normal", c.kanban_state)
        self.assertFalse(c.state_ending)

    def test_signal_close(self):
        """Calling signal close immediately ends the contract"""

        # Start
        start = datetime.now().date() + relativedelta(days=-100)
        today = datetime.now().date()
        end = today + relativedelta(days=100)
        c = self.create_contract("draft", "normal", start, end)
        c.signal_confirm()
        self.assertEqual("open", c.state)
        self.assertEqual("normal", c.kanban_state)
        self.assertFalse(c.state_ending)

        c.signal_close()

        # Ended
        self.assertEqual(today, c.date_end)
        self.assertEqual("close", c.state)
        self.assertEqual("normal", c.kanban_state)
        self.assertFalse(c.state_ending)

    def test_signal_close_ended_contract(self):
        """Calling signal_close() doesn't alter contract end date that is in the past"""

        # Start
        start = datetime.now().date() + relativedelta(days=-100)
        today = datetime.now().date()
        end = today + relativedelta(days=100)
        c = self.create_contract("draft", "normal", start, end)
        c.signal_confirm()
        self.assertEqual("open", c.state)
        self.assertEqual("normal", c.kanban_state)
        self.assertFalse(c.state_ending)

        prev_end = today - relativedelta(days=1)
        c.date_end = prev_end
        c.signal_close()

        # Ended
        self.assertEqual(prev_end, c.date_end)
        self.assertEqual("close", c.state)
        self.assertEqual("normal", c.kanban_state)
        self.assertFalse(c.state_ending)
