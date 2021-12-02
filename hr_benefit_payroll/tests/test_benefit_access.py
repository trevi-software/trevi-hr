# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.tests import new_test_user

from odoo.addons.hr_benefit.tests import common as benefit_common


class TestBenefit(benefit_common.TestBenefitCommon):
    @classmethod
    def setUpClass(cls):
        super(TestBenefit, cls).setUpClass()

        cls.PremiumPayment = cls.env["hr.benefit.premium.payment"]
        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="pm",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
        )
        # Payroll user
        cls.userPU = new_test_user(
            cls.env,
            login="pu",
            groups="base.group_user,payroll.group_payroll_user",
            name="Payroll manager",
        )

    def test_policy_access(self):
        """
        hr.benefit.policy access: Payroll Mgr - read-only, Payroll User read-only
        """

        bn1 = self.create_benefit(self.benefit_create_vals)
        bn2 = self.create_benefit(
            {
                "name": "BenefitB",
                "code": "B",
                "multi_policy": True,
            }
        )
        pol = self.create_policy(self.eeJohn, bn1, date.today())

        # Mgr
        # Succeeds because of payroll user rights
        self.create_succeeds(
            self.userPM,
            self.Policy,
            {
                "name": "tbp",
                "employee_id": self.eeJohn.id,
                "benefit_id": bn2.id,
                "start_date": date.today(),
            },
        )
        self.unlink_fails(self.userPM, pol)
        self.read_succeeds(self.userPM, self.Policy, pol.id)
        self.write_succeeds(self.userPM, self.Policy, pol.id, {"name": "tbp2"})

        # User
        # addons/payroll where payroll officer is created implies group: HR Officer
        self.create_succeeds(
            self.userPU,
            self.Policy,
            {
                "name": "tbp",
                "employee_id": self.eeJohn.id,
                "benefit_id": bn2.id,
                "start_date": date.today(),
            },
        )
        self.unlink_fails(self.userPU, pol)
        self.read_succeeds(self.userPU, self.Policy, pol.id)
        self.write_succeeds(self.userPU, self.Policy, pol.id, {"name": "tbp2"})

    def test_policy_user_own(self):
        """A user can only read his/her own policies"""

        bn1 = self.create_benefit(self.benefit_create_vals)
        polJohn = self.create_policy(self.eeJohn, bn1, date.today())
        polPaul = self.create_policy(self.eePaul, bn1, date.today())
        grpOfficer = self.env.ref("hr.group_hr_user")
        self.assertNotIn(grpOfficer, self.userJohn.groups_id)
        self.assertNotEqual(polJohn, polPaul)
        self.assertEqual(self.userJohn, polJohn.employee_id.user_id)
        self.assertEqual(self.userPaul, polPaul.employee_id.user_id)

        # John can read his own policy
        self.read_succeeds(self.userJohn, self.Policy, polJohn.id)
        # but not Paul's
        self.read_fails(self.userJohn, self.Policy, polPaul.id)
        # John can't modify his own policy or Paul's
        self.write_fails(self.userJohn, self.Policy, polJohn.id, {"note": "A"})
        self.write_fails(self.userJohn, self.Policy, polPaul.id, {"note": "A"})
