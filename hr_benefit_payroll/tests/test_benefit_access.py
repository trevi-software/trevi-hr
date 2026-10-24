# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.tests import new_test_user

from odoo.addons.hr_benefit.tests import common as benefit_common


class TestBenefit(benefit_common.TestBenefitCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
        hr.benefit.policy access: HR Officer - read/write, no unlink.

        In 19.0 ``payroll.group_payroll_user`` implies ``hr.group_hr_manager``
        (payroll officers now manage contracts, which live in ``hr``), so
        payroll users are no longer read-only on benefit policies: they inherit
        the HR manager ACL, which includes unlink. The read-only boundary that
        this test used to exercise now lives on the HR Officer group.
        """

        bn1 = self.create_benefit(self.benefit_create_vals)
        bn2 = self.create_benefit(
            {
                "name": "BenefitB",
                "code": "B",
                "multi_policy": True,
            }
        )

        # Implied groups are resolved transitively by the access checks, they
        # are not stored in ``group_ids``.
        self.assertTrue(self.userPM.has_group("hr.group_hr_manager"))
        self.assertTrue(self.userPU.has_group("hr.group_hr_manager"))

        # Payroll Manager and Payroll User inherit the HR manager rights.
        for user in (self.userPM, self.userPU):
            pol = self.create_policy(self.eeJohn, bn1, date.today())  # noqa: DTZ011
            self.create_succeeds(
                user,
                self.Policy,
                {
                    "name": "tbp",
                    "employee_id": self.eeJohn.id,
                    "benefit_id": bn2.id,
                    "start_date": date.today(),  # noqa: DTZ011
                },
            )
            self.read_succeeds(user, self.Policy, pol.id)
            self.write_succeeds(user, self.Policy, pol.id, {"name": "tbp2"})
            self.unlink_succeeds(user, pol)

        # HR Officer can create and update policies but not delete them.
        pol = self.create_policy(self.eeJohn, bn1, date.today())  # noqa: DTZ011
        self.create_succeeds(
            self.userHRO,
            self.Policy,
            {
                "name": "tbp",
                "employee_id": self.eeJohn.id,
                "benefit_id": bn2.id,
                "start_date": date.today(),  # noqa: DTZ011
            },
        )
        self.read_succeeds(self.userHRO, self.Policy, pol.id)
        self.write_succeeds(self.userHRO, self.Policy, pol.id, {"name": "tbp2"})
        self.unlink_fails(self.userHRO, pol)

    def test_payroll_user_payment_for_other_employee(self):
        """A payroll officer processes payslips of employees that are not his.

        Completing such a payslip creates and updates premium payments, so the
        all-records rule must also apply to create and write.
        """

        bn = self.create_benefit(dict(self.benefit_create_vals, link2payroll=True))
        self.create_premium(bn, amount=100.00)
        pol = self.create_policy(self.eePaul, bn, date.today())  # noqa: DTZ011

        payment = self.create_succeeds(
            self.userPU,
            self.PremiumPayment,
            {
                "employee_id": self.eePaul.id,
                "policy_id": pol.id,
                "amount": 100.00,
            },
        )
        self.write_succeeds(
            self.userPU, self.PremiumPayment, payment.id, {"amount": 90.00}
        )

    def test_policy_user_own(self):
        """A user can only read his/her own policies"""

        bn1 = self.create_benefit(self.benefit_create_vals)
        polJohn = self.create_policy(self.eeJohn, bn1, date.today())  # noqa: DTZ011
        polPaul = self.create_policy(self.eePaul, bn1, date.today())  # noqa: DTZ011
        grpOfficer = self.env.ref("hr.group_hr_user")
        self.assertNotIn(grpOfficer, self.userJohn.group_ids)
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
