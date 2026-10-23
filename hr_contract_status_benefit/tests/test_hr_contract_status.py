# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestContractStatusBenefit(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.Benefit = cls.env["hr.benefit"]
        cls.Policy = cls.env["hr.benefit.policy"]
        cls.Employee = cls.env["hr.employee"]

    def create_employee(self, name="John Smith"):
        return self.Employee.create({"name": name})

    def apply_contract_cron(self):
        # ``hr_contract_status`` owns the "Update Contract Status" cron; it
        # calls ``hr.version.update_status()``, which this module extends.
        cron = self.env.ref("hr_contract_status.ir_cron_data_hr_version_update_status")
        with self.enter_registry_test_mode():
            self.assertTrue(cron.method_direct_trigger())

    def set_contract(self, employee, start, end=None):
        """Set the contract dates of the employee's only contract version.

        ``hr.contract`` is an ``hr.version`` in Odoo 19: an employee always
        owns one version and its contract dates live in ``contract_date_start``
        / ``contract_date_end``.
        """
        contract = employee.version_id
        contract.write({"contract_date_start": start, "contract_date_end": end})
        # The native flags are non-stored computed fields without a declared
        # dependency, so they keep their previous value in the cache after a
        # write; clear it before reading them.
        self.env.invalidate_all()
        return contract

    def create_benefit(self, vals):
        return self.Benefit.create(vals)

    def create_policy(self, employee, benefit, start=False, end=False):
        return self.Policy.create(
            {
                "employee_id": employee.id,
                "benefit_id": benefit.id,
                "start_date": start is False and date.today() or start,  # noqa: DTZ011
                "end_date": end,
            }
        )

    def test_contract_in_effect_opens_policy(self):
        """A policy sharing the contract's start date is opened at contract start"""

        start = date.today() - relativedelta(days=100)  # noqa: DTZ011
        ee = self.create_employee()
        contract = self.set_contract(ee, start)
        self.assertTrue(contract.is_current)

        bn = self.create_benefit({"name": "B", "code": "B"})
        pol = self.create_policy(ee, bn, start)
        self.assertEqual(pol.state, "draft", "The benefit policy is not active yet")

        self.apply_contract_cron()

        self.assertEqual(pol.state, "open", "The benefit policy is now active")

    def test_future_contract_leaves_policy_draft(self):
        """A policy is left alone while its contract has not started"""

        start = date.today() + relativedelta(days=30)  # noqa: DTZ011
        ee = self.create_employee()
        contract = self.set_contract(ee, start)
        self.assertTrue(contract.is_future)

        bn = self.create_benefit({"name": "B", "code": "B"})
        pol = self.create_policy(ee, bn, start)

        self.apply_contract_cron()

        self.assertEqual(pol.state, "draft", "The benefit policy is not active yet")

    def test_policy_with_other_start_date_left_draft(self):
        """Only the policy carrying the contract's start date is opened"""

        start = date.today() - relativedelta(days=100)  # noqa: DTZ011
        ee = self.create_employee()
        self.set_contract(ee, start)

        bn = self.create_benefit({"name": "B", "code": "B"})
        pol = self.create_policy(ee, bn, start + relativedelta(days=10))  # noqa: DTZ011

        self.apply_contract_cron()

        self.assertEqual(pol.state, "draft")

    def test_expired_contract_leaves_policy_draft(self):
        """A contract that has already ended does not activate policies"""

        start = date.today() - relativedelta(days=100)  # noqa: DTZ011
        end = date.today() - relativedelta(days=10)  # noqa: DTZ011
        ee = self.create_employee()
        contract = self.set_contract(ee, start, end)
        self.assertTrue(contract.is_past)

        bn = self.create_benefit({"name": "B", "code": "B"})
        pol = self.create_policy(ee, bn, start)

        self.apply_contract_cron()

        self.assertEqual(pol.state, "draft")
