# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.hr_contract_values.tests.test_hr_contract_init import TestContractInit


class TestPayrollHrContractInit(TestContractInit):
    @classmethod
    def setUpClass(cls):
        super(TestPayrollHrContractInit, cls).setUpClass()

        cls.PPSchedule = cls.env["hr.payroll.period.schedule"]

    def test_no_schedule(self):

        today = fields.Date.today()
        self.HrContractInit.create(
            {
                "name": "Today",
                "date": today,
                "trial_period": 60,
            }
        )
        contract = self.HrContract.create(
            {
                "name": "C1",
                "employee_id": self.eeJohn.id,
            }
        )
        self.assertFalse(contract.pps_id, "Contract pay period schedule field is empty")

    def test_contract_has_schedule(self):

        today = fields.Date.today()
        pps = self.PPSchedule.create(
            {
                "name": "PPS",
                "tz": "Africa/Addis_Ababa",
                "type": "monthly",
                "initial_period_date": today,
            }
        )
        self.HrContractInit.create(
            {
                "name": "Today",
                "date": today,
                "trial_period": 60,
                "pay_sched_id": pps.id,
            }
        )
        contract = self.HrContract.create(
            {
                "name": "C1",
                "employee_id": self.eeJohn.id,
            }
        )
        self.assertEqual(
            contract.pps_id,
            pps,
            "Contract has a default Pay Period Schedule",
        )
