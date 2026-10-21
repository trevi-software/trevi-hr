# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestHrTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # -- Models
        cls.Version = cls.env["hr.version"]
        cls.Department = cls.env["hr.department"]
        cls.Job = cls.env["hr.job"]
        cls.Employee = cls.env["hr.employee"]
        cls.Transfer = cls.env["hr.department.transfer"]
        cls.User = cls.env["res.users"]

        # -- groups
        cls.group_hr_user = cls.env.ref("hr.group_hr_user")
        cls.group_hr_transfer = cls.env.ref("hr_job_transfer.group_hr_transfer")
        cls.group_hr_manager = cls.env.ref("hr.group_hr_manager")

        # -- user
        cls.hr_user = cls.User.create(
            {
                "name": "#Hr User",
                "login": "hruser",
                "group_ids": [(4, cls.group_hr_user.id)],
            }
        )
        cls.hr_officer = cls.User.create(
            {
                "name": "#Hr Officer",
                "login": "hroffcer",
                "group_ids": [(4, cls.group_hr_transfer.id)],
            }
        )

        # -- departments
        cls.dpt_temp = cls.Department.create({"name": "#Temp"})
        cls.dpt_parttime = cls.Department.create({"name": "#Parttime"})

        # -- jobs
        cls.job_trainee = cls.Job.create(
            {"name": "#trainee", "department_id": cls.dpt_temp.id}
        )
        cls.job_consultant = cls.Job.create(
            {
                "name": "#consultant",
                "department_id": cls.dpt_parttime.id,
            }
        )

        # -- dates
        cls.two_month_ago = fields.Date.today() - relativedelta(days=60)
        cls.today = fields.Date.today()
        cls.after_one_month = fields.Date.today() + relativedelta(days=30)

    def create_employee(self, name, job_id):
        return self.Employee.with_user(self.hr_officer).create(
            [
                {
                    "name": name,
                    "job_id": self.Employee.browse(job_id).id,
                }
            ]
        )

    def create_contract(self, employee, start, end=None, trial_end=None, user=False):
        """Give the employee's version a running contract.

        Odoo 19 replaced ``hr.contract`` with ``hr.version``: every employee
        owns one version (delegated through ``_inherits``) and its contract is
        described by the native dates instead of a ``state``/``kanban_state``
        pair.
        """
        _user = self.hr_user if not user else user
        contract = employee.version_id
        vals = {
            "contract_date_start": start,
            "date_version": start,
        }
        if end:
            vals["contract_date_end"] = end
        if trial_end:
            vals["trial_date_end"] = trial_end
        contract.with_user(_user).write(vals)
        return contract

    def apply_transfer_cron(self):
        cron = self.env.ref("hr_job_transfer.hr_department_transfer_cron")
        # The cron body runs on its own cursor; in registry test mode that
        # cursor wraps the test one, so its writes are visible (and rolled
        # back) with the test transaction.
        with self.enter_registry_test_mode():
            # method_direct_trigger() returns True on success, and an action
            # dict when the job raised.
            self.assertTrue(cron.method_direct_trigger() is True)

    def test_only_draft_transfer_can_be_deleted(self):
        employee = self.create_employee("#John", self.job_trainee.id)
        contract = self.create_contract(
            employee=employee,
            start=self.two_month_ago,
            end=self.after_one_month,
            user=self.hr_officer,
        )
        transfer1 = self.Transfer.with_user(self.hr_officer).create(
            {
                "employee_id": employee.id,
                "dst_id": self.job_consultant.id,
                "date": self.today,
            }
        )
        self.assertEqual(transfer1.src_id, contract.job_id)
        self.assertTrue(transfer1.src_contract_id.is_in_contract)
        self.assertEqual(transfer1.state, "draft")
        transfer1.unlink()

        transfer2 = self.Transfer.with_user(self.hr_officer).create(
            {
                "employee_id": employee.id,
                "dst_id": self.job_consultant.id,
                "date": self.today,
            }
        )
        self.assertTrue(transfer2.src_contract_id.is_in_contract)
        self.assertEqual(transfer2.state, "draft")

        transfer2.action_confirm()
        self.assertEqual(transfer2.state, "confirm")
        with self.assertRaises(UserError):
            transfer2.unlink()

        transfer2.action_transfer()
        self.assertEqual(transfer2.state, "done")
        # The transfer closes the old version and opens a new one on the
        # destination job.
        self.assertTrue(transfer2.dst_contract_id)
        self.assertEqual(transfer2.dst_contract_id.job_id, self.job_consultant)
        self.assertEqual(transfer2.dst_contract_id.contract_date_start, self.today)
        with self.assertRaises(UserError):
            transfer2.unlink()

    def test_only_users_in_transfer_group_can_manage_transfer(self):
        employee = self.create_employee("#John", self.job_trainee.id)
        self.create_contract(
            employee=employee,
            start=self.two_month_ago,
            end=self.after_one_month,
            user=self.hr_officer,
        )
        transfer = self.Transfer.with_user(self.hr_user).create(
            {
                "employee_id": employee.id,
                "dst_id": self.job_consultant.id,
                "date": self.today,
            }
        )
        self.assertEqual(transfer.state, "draft")
        with self.assertRaises(AccessError):
            transfer.action_confirm()

        transfer.with_user(self.hr_officer).action_confirm()
        self.assertEqual(transfer.state, "confirm")
        with self.assertRaises(AccessError):
            transfer.action_transfer()

        transfer.with_user(self.hr_officer).action_transfer()
        self.assertEqual(transfer.state, "done")

    def test_transfer_on_inactive_contract_is_not_allowed(self):
        employee = self.create_employee("#John", self.job_trainee.id)
        contract = self.create_contract(
            employee=employee,
            start=self.two_month_ago,
            end=self.after_one_month,
            user=self.hr_officer,
        )
        transfer = self.Transfer.with_user(self.hr_user).create(
            {
                "employee_id": employee.id,
                "dst_id": self.job_consultant.id,
                "date": self.today,
            }
        )
        transfer.with_user(self.hr_officer).action_confirm()
        self.assertEqual(transfer.state, "confirm")
        # End the contract: in 18.0 this was signal_close(), which set the
        # custom state to "close"; the 19.0 equivalent is the native end date.
        contract.contract_date_end = self.today
        with self.assertRaises(UserError):
            transfer.with_user(self.hr_officer).action_transfer()

    def test_cron_transfer(self):
        employee = self.create_employee("#John", self.job_trainee.id)
        self.create_contract(
            employee=employee,
            start=self.two_month_ago,
            end=self.after_one_month,
            user=self.hr_officer,
        )
        transfer = self.Transfer.with_user(self.hr_user).create(
            {
                "employee_id": employee.id,
                "dst_id": self.job_consultant.id,
                "date": self.today + relativedelta(days=1),
            }
        )
        transfer.with_user(self.hr_officer).action_confirm()
        self.assertEqual(transfer.state, "pending")
        transfer.date = self.today
        self.apply_transfer_cron()
        self.assertEqual(transfer.state, "done")
