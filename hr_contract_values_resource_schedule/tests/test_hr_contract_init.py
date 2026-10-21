# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.tests import common


class TestContractInit(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.HrEmployee = cls.env["hr.employee"]
        # Odoo 19 merged ``hr_contract`` into ``hr``: ``hr.contract`` is now
        # ``hr.version``, which is what carries the contract data.
        cls.HrVersion = cls.env["hr.version"]
        cls.ResourceCalendar = cls.env["resource.calendar"]
        cls.HrContractInit = cls.env["hr.contract.init"]

        # Do not rely on demo data: create the working hours we need.  A
        # calendar other than the company's default one is used so that the
        # assertions below really check the value coming from the contract
        # settings.
        cls.std35_calendar = cls.ResourceCalendar.create(
            {"name": "Standard 35 hours/week"}
        )

        # The employee always owns a version, so it is backdated to leave
        # today's effective date free for the version created by the test.
        cls.eeJohn = cls.HrEmployee.create(
            {"name": "John", "date_version": "2000-01-01"}
        )

    def test_load_from_policy(self):
        self.HrContractInit.create(
            {
                "name": "Contract Default values",
                "date": fields.Date.today(),
                "trial_period": 60,
                "resource_calendar_id": self.std35_calendar.id,
            }
        )

        contract = self.HrVersion.create(
            {
                "name": "C1",
                "employee_id": self.eeJohn.id,
                "wage": 1.0,
            }
        )
        self.assertEqual(
            contract.resource_calendar_id,
            self.std35_calendar,
            "The work calendar in the contract is the one from the default values",
        )
        self.assertEqual(
            contract.employee_id.resource_id.calendar_id,
            self.std35_calendar,
            "The work calendar in the resource is the one from the default values",
        )
