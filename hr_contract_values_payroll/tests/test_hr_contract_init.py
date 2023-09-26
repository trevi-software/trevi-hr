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
        cls.HrPayrollStruct = cls.env["hr.payroll.structure"]
        cls.HrContractInit = cls.env["hr.contract.init"]

        cls.eeJohn = cls.HrEmployee.create({"name": "John"})

    def test_load_latest_values(self):
        """Initial values are loaded from the latest values"""

        psA = self.HrPayrollStruct.create({"name": "S A", "code": "A"})
        psB = self.HrPayrollStruct.create({"name": "S B", "code": "B"})
        countInits = self.HrContractInit.search_count([])

        # Create two init values
        self.HrContractInit.create(
            {
                "name": "Way in the past",
                "date": "2000-01-01",
                "trial_period": 45,
                "struct_id": psA.id,
            }
        )
        self.HrContractInit.create(
            {
                "name": "Today",
                "date": fields.Date.today(),
                "trial_period": 60,
                "struct_id": psB.id,
            }
        )

        contract = self.HrContract.create(
            {
                "name": "C1",
                "employee_id": self.eeJohn.id,
                "wage": 1.0,
            }
        )
        cInits = self.HrContractInit.search([])
        self.assertEqual(countInits + 2, len(cInits))
        self.assertEqual(psB.id, contract.struct_id.id)
