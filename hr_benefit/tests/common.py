# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestBenefitCommon(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestBenefitCommon, cls).setUpClass()

        cls.Benefit = cls.env["hr.benefit"]
        cls.Premium = cls.env["hr.benefit.premium"]
        cls.Earning = cls.env["hr.benefit.advantage"]
        cls.Policy = cls.env["hr.benefit.policy"]
        cls.Claim = cls.env["hr.benefit.claim"]
        cls.EndWizard = cls.env["hr.benefit.policy.end"]
        cls.EnrollWizard = cls.env["hr.benefit.enroll.employee"]
        cls.EnrollMultiWizard = cls.env["hr.benefit.enroll.multi.employee"]

        # Normal User John
        cls.userJohn = new_test_user(
            cls.env,
            login="john",
            groups="base.group_user",
            name="John",
        )
        cls.eeJohn = cls.env["hr.employee"].create(
            {"name": "John", "user_id": cls.userJohn.id}
        )

        # Normal User Paul
        cls.userPaul = new_test_user(
            cls.env,
            login="paul",
            groups="base.group_user",
            name="Paul",
        )
        cls.eePaul = cls.env["hr.employee"].create(
            {"name": "Paul", "user_id": cls.userPaul.id}
        )

        cls.benefit_create_vals = {"name": "A", "code": "A"}

        # HR Manager
        cls.userHRM = new_test_user(
            cls.env,
            login="hrm",
            groups="base.group_user,hr.group_hr_manager",
            name="Payroll manager",
            email="hrm@example.com",
        )
        # HR User
        cls.userHRO = new_test_user(
            cls.env,
            login="hro",
            groups="base.group_user,hr.group_hr_user",
            name="Payroll officer",
            email="hro@example.com",
        )

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

    def create_premium(
        self, benefit, start=False, ptype="monthly", amount=0, total=False
    ):
        _dict = {
            "benefit_id": benefit.id,
            "effective_date": start is False and date.today() or start,
            "type": ptype,
            "amount": amount,
        }
        if total is not False:
            _dict["total_amount"] = total
        benefit.has_premium = True
        return self.Premium.create(_dict)

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

    def create_claim(self, policy, amount, dt=None):
        if dt is None:
            dt = date.today()
        return self.Claim.create(
            {
                "date": dt,
                "benefit_policy_id": policy.id,
                "employee_id": policy.employee_id.id,
                "amount_requested": amount,
            }
        )

    def create_benefit(self, vals):

        return self.Benefit.create(vals)

    def create_contract(self, state, kanban_state, start, end=None, trial_end=None):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": self.eeJohn.id,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
            }
        )

    def create_fails(self, user, obj, vals):
        with self.assertRaises(AccessError):
            obj.with_user(user).create(vals)

    def create_succeeds(self, user, obj, vals):
        res = None
        try:
            res = obj.with_user(user).create(vals)
        except AccessError:
            self.fail("Caught unexpected exception creating {}".format(obj._name))
        return res

    def unlink_fails(self, user, obj):
        with self.assertRaises(AccessError):
            obj.with_user(user).unlink()

    def unlink_succeeds(self, user, obj):
        try:
            obj.with_user(user).unlink()
        except AccessError:
            self.fail("Caught unexpected exception unlinking {}".format(obj._name))

    def read_succeeds(self, user, obj, obj_id):
        try:
            obj.with_user(user).browse(obj_id).read([])
        except AccessError:
            self.fail("Caught an unexpected exception reading {}".format(obj._name))

    def read_fails(self, user, obj, obj_id):
        with self.assertRaises(AccessError):
            obj.with_user(user).browse(obj_id).read([])

    # Pre-requisite: READ Access
    def write_fails(self, user, obj, obj_id, write_vals):
        with self.assertRaises(AccessError):
            obj.with_user(user).browse(obj_id).write(write_vals)

    # Pre-requisite: READ Access
    def write_succeeds(self, user, obj, obj_id, write_vals):
        try:
            obj.with_user(user).browse(obj_id).write(write_vals)
        except AccessError:
            self.fail("Caught an unexpected exception writing {}".format(obj._name))
