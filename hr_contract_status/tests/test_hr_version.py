# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common


class TestContractStatus(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrVersion = cls.env["hr.version"]
        cls.Dept = cls.env["hr.department"]
        cls.Job = cls.env["hr.job"]

        cls.dept_rnd = cls.Dept.create({"name": "R&D"})
        cls.job_ux_designer = cls.Job.create(
            {"name": "#UX Designer", "department_id": cls.dept_rnd.id}
        )

    def create_employee(self, name="John", **vals):
        return self.HrEmployee.create(dict({"name": name}, **vals))

    def set_contract(self, employee, start=None, end=None, trial_end=None):
        """Set the dates of the employee's only contract version.

        ``hr.employee`` always owns one version; writing the contract dates on
        it is how a contract is created through the employee form in 19.0.
        """
        contract = employee.version_id
        vals = {}
        if start:
            vals["contract_date_start"] = start
            if end:
                vals["contract_date_end"] = end
        if trial_end:
            vals["trial_date_end"] = trial_end
        contract.write(vals)
        return contract

    def apply_cron(self):
        cron = self.env.ref("hr_contract_status.ir_cron_data_hr_version_update_status")
        # The cron job runs on its own cursor/transaction; the Odoo test API
        # makes it wrap the current one so it can see (and roll back with) the
        # test data.
        with self.enter_registry_test_mode():
            self.assertTrue(cron.method_direct_trigger())

    def test_department_comes_from_job(self):
        """A contract takes the department of the job it is attached to"""

        employee = self.create_employee(job_id=self.job_ux_designer.id)

        self.assertEqual(self.job_ux_designer, employee.version_id.job_id)
        self.assertEqual(self.dept_rnd, employee.version_id.department_id)
        self.assertEqual(self.dept_rnd, employee.department_id)

    def test_trial_ending(self):
        """A trial period inside the notice period is flagged and notified"""

        today = fields.Date.today()
        employee = self.create_employee()
        contract = self.set_contract(
            employee,
            start=today + relativedelta(days=-10),
            trial_end=today + relativedelta(days=5),
        )

        self.assertFalse(contract.trial_ending)
        self.assertFalse(contract.activity_ids)

        self.apply_cron()

        self.assertTrue(contract.trial_ending)
        self.assertEqual(1, len(contract.activity_ids))
        self.assertEqual(contract.trial_date_end, contract.activity_ids.date_deadline)

    def test_trial_not_ending(self):
        """A trial period outside the notice period is left alone"""

        today = fields.Date.today()
        employee = self.create_employee()
        contract = self.set_contract(
            employee,
            start=today + relativedelta(days=-10),
            trial_end=today + relativedelta(days=100),
        )

        self.apply_cron()

        self.assertFalse(contract.trial_ending)
        self.assertFalse(contract.activity_ids)

    def test_trial_ending_cleared(self):
        """A trial period that ended is no longer flagged"""

        today = fields.Date.today()
        employee = self.create_employee()
        contract = self.set_contract(
            employee,
            start=today + relativedelta(days=-10),
            trial_end=today + relativedelta(days=5),
        )

        self.apply_cron()
        self.assertTrue(contract.trial_ending)

        contract.trial_date_end = today + relativedelta(days=-1)
        self.apply_cron()

        self.assertFalse(contract.trial_ending)

    def test_trial_ending_notified_once(self):
        """Running the cron twice does not schedule a second activity"""

        today = fields.Date.today()
        employee = self.create_employee()
        contract = self.set_contract(
            employee,
            start=today + relativedelta(days=-10),
            trial_end=today + relativedelta(days=5),
        )

        self.apply_cron()
        self.apply_cron()

        self.assertEqual(1, len(contract.activity_ids))

    def test_contract_ending(self):
        """A contract inside the notice period is flagged"""

        today = fields.Date.today()
        employee = self.create_employee()
        contract = self.set_contract(
            employee,
            start=today + relativedelta(days=-100),
            end=today + relativedelta(days=5),
        )

        self.assertFalse(contract.state_ending)

        self.apply_cron()
        self.assertTrue(contract.state_ending)

        # moved outside of the notice period again
        contract.contract_date_end = today + relativedelta(days=20)
        self.apply_cron()

        self.assertFalse(contract.state_ending)

    def test_contract_ended(self):
        """An expired contract is no longer flagged"""

        today = fields.Date.today()
        employee = self.create_employee()
        contract = self.set_contract(
            employee,
            start=today + relativedelta(days=-100),
            end=today + relativedelta(days=5),
        )

        self.apply_cron()
        self.assertTrue(contract.state_ending)

        contract.contract_date_end = today + relativedelta(days=-1)
        self.apply_cron()

        self.assertFalse(contract.state_ending)

    def test_alert_subtypes(self):
        """The alert subtypes follow the ending flags"""

        employee = self.create_employee()
        contract = employee.version_id

        contract.trial_ending = True
        self.assertEqual(
            self.env.ref("hr_contract_status.mt_alert_trial_ending"),
            contract._track_subtype({"trial_ending": False}),
        )

        contract.trial_ending = False
        contract.state_ending = True
        self.assertEqual(
            self.env.ref("hr_contract_status.mt_alert_contract_ending"),
            contract._track_subtype({"state_ending": False}),
        )
