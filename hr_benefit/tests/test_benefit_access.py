# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from . import common


class TestBenefitAccess(common.TestBenefitCommon):
    def test_benefit_access(self):
        """hr.benefit access: HRM - full access, HRO read-only"""

        bn = self.create_benefit(self.benefit_create_vals)

        # HRM
        self.create_succeeds(self.userHRM, self.Benefit, self.benefit_create_vals)
        self.read_succeeds(self.userHRM, self.Benefit, bn.id)
        self.write_succeeds(self.userHRM, self.Benefit, bn.id, {"name": "tba"})
        self.unlink_succeeds(self.userHRM, bn)

        # HRO
        self.create_fails(self.userHRO, self.Benefit, self.benefit_create_vals)
        self.unlink_fails(self.userHRO, bn)
        self.read_succeeds(self.userHRO, self.Benefit, bn.id)
        self.write_fails(self.userHRO, self.Benefit, bn.id, {"name": "tba"})

    def test_premium_access(self):
        """hr.benefit.premium access: HRM - full access, HRO read-only"""

        bn = self.create_benefit(self.benefit_create_vals)
        create_vals = {
            "benefit_id": bn.id,
            "effective_date": date.today(),
            "type": "monthly",
        }
        prm = self.create_premium(bn, date.today() + relativedelta(days=30))

        # HRM
        self.create_succeeds(self.userHRM, self.Premium, create_vals)
        self.unlink_succeeds(self.userHRM, prm)
        self.read_succeeds(self.userHRM, self.Premium, prm.id)
        self.write_succeeds(self.userHRM, self.Premium, prm.id, {"type": "annual"})

        # HRO
        self.create_fails(self.userHRO, self.Premium, create_vals)
        self.unlink_fails(self.userHRO, prm)
        self.read_succeeds(self.userHRO, self.Premium, prm.id)
        self.write_fails(self.userHRO, self.Premium, prm.id, {"type": "annual"})

    def test_earning_access(self):
        """hr.benefit.advantage access: HRM - full access, HRO read-only"""

        bn = self.create_benefit(self.benefit_create_vals)
        create_vals = {
            "benefit_id": bn.id,
            "effective_date": date.today(),
            "type": "allowance",
        }
        earn = self.create_earning(bn, date.today() + relativedelta(days=30))

        # HRM
        self.create_succeeds(self.userHRM, self.Earning, create_vals)
        self.unlink_succeeds(self.userHRM, earn)
        self.read_succeeds(self.userHRM, self.Earning, earn.id)
        self.write_succeeds(self.userHRM, self.Earning, earn.id, {"type": "reimburse"})

        # HRO
        self.create_fails(self.userHRO, self.Earning, create_vals)
        self.unlink_fails(self.userHRO, earn)
        self.read_succeeds(self.userHRO, self.Earning, earn.id)
        self.write_fails(self.userHRO, self.Earning, earn.id, {"type": "reimburse"})

    def test_policy_access(self):
        """hr.benefit.policy access: HRM - full access, HRO read-only"""

        bn1 = self.create_benefit(self.benefit_create_vals)
        bn2 = self.create_benefit(
            {
                "name": "BenefitB",
                "code": "B",
                "multi_policy": True,
            }
        )
        pol = self.create_policy(self.eeJohn, bn1, date.today())

        # HRM
        hroPol = self.create_succeeds(
            self.userHRM,
            self.Policy,
            {
                "name": "tbp",
                "employee_id": self.eeJohn.id,
                "benefit_id": bn2.id,
                "start_date": date.today(),
            },
        )
        self.unlink_succeeds(self.userHRM, hroPol)
        self.read_succeeds(self.userHRM, self.Policy, pol.id)
        self.write_succeeds(self.userHRM, self.Policy, pol.id, {"name": "tbp2"})

        # HRO
        hroPol = self.create_succeeds(
            self.userHRO,
            self.Policy,
            {
                "name": "tbp",
                "employee_id": self.eeJohn.id,
                "benefit_id": bn2.id,
                "start_date": date.today(),
            },
        )
        self.unlink_fails(self.userHRO, hroPol)
        self.read_succeeds(self.userHRO, self.Policy, pol.id)
        self.write_succeeds(self.userHRO, self.Policy, pol.id, {"name": "tbp2"})

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
