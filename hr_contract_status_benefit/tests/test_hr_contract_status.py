# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestEmployeeStatus(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Benefit = cls.env["hr.benefit"]
        cls.Earning = cls.env["hr.benefit.advantage"]
        cls.Policy = cls.env["hr.benefit.policy"]
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

    def test_hire_employee_signal(self):

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "normal", start, trial_end=end)
        cc.trial_date_end = date.today() - relativedelta(days=1)
        self.assertEqual("new", ee.status)

        # create benefit policy
        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, date.today() - relativedelta(days=100), allowance=1000)
        pol = self.create_policy(ee, bn, date.today() - relativedelta(days=100))
        self.assertEqual(pol.state, "draft", "The benefit policy is not active yet")

        # Open contract
        cc.signal_confirm()

        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)
        self.assertEqual(pol.state, "open", "The benefit policy is now active")

    def test_hire_employee_cron(self):

        start = date.today() - relativedelta(days=100)
        end = date.today() + relativedelta(days=60)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, trial_end=end)
        cc.trial_date_end = date.today() - relativedelta(days=1)
        self.assertEqual("new", ee.status)

        # create benefit policy
        bn = self.create_benefit({"name": "B", "code": "B"})
        self.create_earning(bn, start, allowance=1000)
        pol = self.create_policy(ee, bn, start)
        self.assertEqual(pol.state, "draft", "The benefit policy is not active yet")

        # Open contract
        self.apply_contract_cron()

        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)
        self.assertEqual(pol.state, "open", "The benefit policy is now active")
