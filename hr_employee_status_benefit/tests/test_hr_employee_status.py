# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestEmployeeStatus(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.Benefit = cls.env["hr.benefit"]
        cls.Earning = cls.env["hr.benefit.advantage"]
        cls.Policy = cls.env["hr.benefit.policy"]
        cls.Employee = cls.env["hr.employee"]
        # Odoo 19 merged ``hr_contract`` into ``hr``: a contract is now an
        # ``hr.version`` and the trevi contract state machine is gone.
        cls.Version = cls.env["hr.version"]
        cls.Separation = cls.env["hr.employee.termination"]

        cls.reason = cls.env["hr.employee.termination.reason"].create(
            {"name": "Retired"}
        )

    def create_employee(self, name="John Smith"):
        # An employee always owns at least one version; it is backdated so that
        # the versions created by the tests can start in the past and be the
        # employee's current one.
        return self.Employee.create(
            {
                "name": name,
                "date_version": "2000-01-01",
            }
        )

    def apply_contract_cron(self):
        # ``hr_contract.ir_cron_data_contract_update_state`` does not exist in
        # 19.0; the closest replacement is the core hr cron that keeps every
        # employee's current version up to date.
        self.env.ref(
            "hr.ir_cron_data_employee_update_current_version"
        ).method_direct_trigger()

    def create_contract(self, employee, start, end=None, trial_end=None):
        """Create a running contract.

        In 18.0 this was an ``hr.contract`` created as ``draft`` + ``done`` and
        then confirmed with ``signal_confirm()``. In 19.0 a contract is an
        ``hr.version``: its start/end dates are ``contract_date_start`` /
        ``contract_date_end`` and its state is described by the native
        ``active`` / ``is_current`` flags instead of the dropped
        ``state`` / ``kanban_state`` selection.

        ``date_version`` is pinned to the contract start date so the version is
        the employee's current one (``current_version_id`` is the version with
        the highest ``date_version`` not in the future).
        """
        return self.Version.create(
            {
                "name": "Contract",
                "employee_id": employee.id,
                "wage": 1,
                "date_version": start,
                "contract_date_start": start,
                "trial_date_end": trial_end,
                "contract_date_end": end,
            }
        )

    def create_benefit(self, vals):
        return self.Benefit.create(vals)

    def create_earning(
        self,
        benefit,
        start=False,
        ptype="allowance",
        limit=0,
        limit_period="monthly",
        limit_mo_day="1",
        allowance=0,
        loan=0,
        mindays=0,
    ):
        _dict = {
            "benefit_id": benefit.id,
            "effective_date": start is False and date.today() or start,
            "type": ptype,
            "allowance_amount": allowance,
            "loan_amount": loan,
            "min_employed_days": mindays,
        }
        if ptype == "reimburse":
            _dict["reim_limit_amount"] = limit
            _dict["reim_limit_period"] = limit_period
            _dict["reim_period_month_day"] = limit_mo_day
        benefit.has_advantage = True
        return self.Earning.create(_dict)

    def create_policy(
        self,
        employee,
        benefit,
        start=False,
        end=False,
        advantage=False,
        premium=False,
        premium_total=False,
    ):
        _dict = {
            "employee_id": employee.id,
            "benefit_id": benefit.id,
            "start_date": start is False and date.today() or start,
            "end_date": end,
        }
        if advantage is not False:
            _dict["advantage_override"] = True
            _dict["advantage_amount"] = advantage
        if premium is not False:
            _dict["premium_override"] = True
            _dict["premium_override_amount"] = premium
            _dict["premium_override_total"] = premium_total
        return self.Policy.create(_dict)

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

    def test_deactivate_employee(self):
        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(
            ee, start, end, trial_end=date.today() - relativedelta(days=1)
        )
        self.assertEqual("new", ee.status)

        # The version has started and its trial period is over: it is the
        # employee's running contract. There is no 'draft' -> 'open' workflow
        # any more, the native flags say so.
        self.assertTrue(cc.active)
        self.assertTrue(cc.is_current)
        # In 18.0 the employee moved to 'active' as a side effect of confirming
        # the contract (hr_contract_status.signal_confirm()). That state machine
        # is gone in 19.0, so set the precondition directly - what this test
        # exercises is the benefit-policy behaviour around separation and
        # deactivation, not the removed workflow.
        ee.write({"status": "active"})
        self.assertEqual("active", ee.status)

        # create benefit policy
        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today() - relativedelta(days=100), allowance=1000)
        pol = self.create_policy(ee, bn, date.today() - relativedelta(days=100))
        pol.state_open()
        self.assertEqual(pol.state, "open", "The benefit policy is open and running")

        # Create separation
        sep = self.create_separation(ee, date.today())
        self.assertEqual(ee.status, "separation", "The employee is pending separation")
        self.assertTrue(cc.is_current, "The contract is still running")
        self.assertEqual(pol.state, "open", "The benefit policy is still open")

        sep.signal_done()

        self.assertEqual(pol.state, "done", "The benefit policy has also ended")
        self.assertEqual(
            pol.end_date,
            sep.name,
            "The separation record and benefit policy end date are the same",
        )
