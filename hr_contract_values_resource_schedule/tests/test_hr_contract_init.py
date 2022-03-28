# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.tests import common


class TestContractInit(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestContractInit, cls).setUpClass()

        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.ResourceCalendar = cls.env["resource.calendar"]
        cls.HrContractInit = cls.env["hr.contract.init"]

        cls.eeJohn = cls.HrEmployee.create({"name": "John"})
        cls.std35_calendar = cls.env.ref("resource.resource_calendar_std_35h")

    def test_load_from_policy(self):

        self.HrContractInit.create(
            {
                "name": "Contract Default values",
                "date": fields.Date.today(),
                "trial_period": 60,
                "resource_calendar_id": self.std35_calendar.id,
            }
        )

        contract = self.HrContract.create(
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
