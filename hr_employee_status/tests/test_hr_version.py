# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestHrVersion(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.Employee = cls.env["hr.employee"]
        cls.Version = cls.env["hr.version"]
        cls.VersionEnd = cls.env["hr.version.end"]
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

    def test_contract_autoclose(self):
        """An ended contract starts the employee de-activation process"""

        start = date.today() - relativedelta(days=100)
        end = date.today() - relativedelta(days=1)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.assertEqual("new", ee.status)
        self.assertTrue(cc.is_past)

        self.update_status()

        self.assertEqual(1, len(ee.inactive_ids))
        self.assertEqual(end, ee.inactive_ids.name)
        self.assertEqual("Contract Ended", ee.inactive_ids.reason_id.name)
        self.assertEqual("separation", ee.status)
        self.assertEqual(end, cc.contract_date_end)

    def test_contract_autoclose_no_duplicate_separation(self):
        """The de-activation process is not started twice for one contract"""

        start = date.today() - relativedelta(days=100)
        end = date.today() - relativedelta(days=1)
        ee = self.create_employee()
        self.create_contract(ee, start, end)

        self.update_status()
        self.assertEqual(1, len(ee.inactive_ids))

        self.update_status()
        self.assertEqual(1, len(ee.inactive_ids))
        self.assertEqual("separation", ee.status)

    def test_contract_autoclose_keeps_running_contract(self):
        """An ended contract does not de-activate an employee that is
        still under contract"""

        old = self.create_contract(
            self.create_employee(),
            date.today() - relativedelta(days=200),
            date.today() - relativedelta(days=50),
        )
        ee = old.employee_id
        new = self.Version.create(
            {
                "employee_id": ee.id,
                "date_version": date.today() - relativedelta(days=40),
                "contract_date_start": date.today() - relativedelta(days=40),
            }
        )

        self.update_status()

        self.assertEqual(0, len(ee.inactive_ids))
        self.assertEqual("active", ee.status)
        self.assertTrue(old.is_past)
        self.assertTrue(new.is_in_contract)

    def test_end_contract_wizard(self):
        """'End Contract' wizard creates a separation and ends the contract"""

        start = date.today() - relativedelta(days=100)
        ee = self.create_employee()
        cc = self.create_contract(ee, start)

        cend = self.VersionEnd.create(
            {
                "version_id": cc.id,
                "employee_id": ee.id,
                "reason_id": self.reason.id,
                "date": date.today(),
            }
        )
        cend.set_employee_inactive()

        self.assertEqual(1, len(ee.inactive_ids))
        self.assertEqual(date.today(), ee.inactive_ids.name)
        self.assertEqual("separation", ee.status)
        self.assertEqual(date.today(), cc.contract_date_end)
        # the contract was open ended before the separation
        self.assertFalse(ee.inactive_ids.contract_date_end)

    def test_end_contract_action(self):
        """The 'End Contract' action hands the version to the wizard"""

        start = date.today() - relativedelta(days=100)
        ee = self.create_employee()
        cc = self.create_contract(ee, start)

        action = ee.action_end_contract()
        self.assertEqual("hr.version.end", action["res_model"])
        self.assertEqual(cc.id, action["context"]["end_version_id"])

    def test_signal_reactivate_cancels_pending_separation(self):
        """The 'Re-Activate' action cancels a pending separation

        Otherwise the daily separation job would archive the employee again
        on the separation's effective date.
        """

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.update_status()
        self.assertEqual("active", ee.status)

        self.Separation.create(
            {
                "name": sep_date,
                "reason_id": self.reason.id,
                "employee_id": ee.id,
            }
        )
        self.assertEqual("separation", ee.status)
        self.assertEqual(sep_date, cc.contract_date_end)

        ee.signal_reactivate()

        self.assertEqual("active", ee.status)
        self.assertTrue(ee.active)
        self.assertEqual(end, cc.contract_date_end)
        self.assertFalse(
            self.Separation.search(
                [
                    ("employee_id", "=", ee.id),
                    ("state", "in", ["draft", "confirm"]),
                ]
            )
        )

    def test_unlink_cancelled_separation_keeps_current_dates(self):
        """Deleting a cancelled separation leaves the current one alone"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        new_sep_date = date.today() + relativedelta(days=40)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)
        self.update_status()

        old = self.Separation.create(
            {
                "name": sep_date,
                "reason_id": self.reason.id,
                "employee_id": ee.id,
            }
        )
        old.signal_cancel()
        self.assertEqual(end, cc.contract_date_end)

        new = self.Separation.create(
            {
                "name": new_sep_date,
                "reason_id": self.reason.id,
                "employee_id": ee.id,
            }
        )
        self.assertEqual("separation", ee.status)
        self.assertEqual(new_sep_date, cc.contract_date_end)

        old.unlink()

        self.assertTrue(new.exists())
        self.assertEqual("separation", ee.status)
        self.assertEqual(new_sep_date, cc.contract_date_end)

    def test_re_activate(self):
        """Re-activating cancels a pending separation and re-opens the contract"""

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=100)
        sep_date = date.today() + relativedelta(days=5)
        ee = self.create_employee()
        cc = self.create_contract(ee, start, end)

        self.update_status()
        self.assertEqual("active", ee.status)

        self.Separation.create(
            {
                "name": sep_date,
                "reason_id": self.reason.id,
                "employee_id": ee.id,
            }
        )
        self.assertEqual("separation", ee.status)
        self.assertEqual(sep_date, cc.contract_date_end)

        cc.re_activate()

        self.assertEqual("active", ee.status)
        self.assertTrue(ee.active)
        self.assertFalse(self.Separation.search([("employee_id", "=", ee.id)]))
        self.assertEqual(end, cc.contract_date_end)
