# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.tests import new_test_user

from odoo.addons.payroll_periods.tests.test_payroll_period_schedule import TestSchedule


class TestScheduleOperatingUnit(TestSchedule):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.OU = cls.env["operating.unit"]
        cls.Users = cls.env["res.users"]

        # Operating Units
        cls.ou_main = cls.OU.create(
            {"name": "Main", "code": "M", "partner_id": cls.env.company.id}
        )
        cls.ou_second = cls.OU.create(
            {"name": "Second", "code": "S", "partner_id": cls.env.company.id}
        )

        # Users
        cls.user1 = new_test_user(
            cls.env,
            login="user1",
            name="User 1",
            email="user1@example.org",
            groups="base.group_user,payroll.group_payroll_manager",
            operating_unit_ids=[(4, ou.id) for ou in [cls.ou_main, cls.ou_second]],
        )
        cls.user2 = new_test_user(
            cls.env,
            login="user2",
            name="User 2",
            email="user1@example.org",
            groups="base.group_user,payroll.group_payroll_manager",
            operating_unit_ids=[(4, ou.id) for ou in [cls.ou_second]],
        )

    def test_period_per_ou(self):
        """One period is created for each OU"""

        pps = self.create_payroll_schedule("monthly", date(2021, 1, 1))
        pps.use_operating_units = True
        pps.button_add_pay_periods()

        len_ou = len(self.OU.search([]).ids)
        listPP = self.Period.search([])
        self.assertEqual(
            len(listPP), len_ou, "There is one period for each Operating Unit"
        )
        for pp in listPP:
            self.assertIn(
                pp.operating_unit_id.name,
                pp.name,
                "The pay period contains the Operating Unit's name",
            )

        listPP = self.Period.search(
            [("operating_unit_id", "in", [self.ou_main.id, self.ou_second.id])]
        )
        self.assertEqual(len(listPP), 2, "I found the two OUs created for this test")
        self.assertEqual(
            listPP[0].operating_unit_id,
            self.ou_second,
        )
        self.assertEqual(
            listPP[1].operating_unit_id,
            self.ou_main,
        )
        self.assertNotEqual(
            listPP[0].operating_unit_id,
            listPP[1].operating_unit_id,
            "Each period is for a different Operating Unit",
        )
