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
        # Odoo 19 merged ``hr_contract`` into ``hr``: the contract (and so the
        # payroll structure) now lives on ``hr.version``.
        cls.HrVersion = cls.env["hr.version"]
        cls.HrPayrollStruct = cls.env["hr.payroll.structure"]
        cls.HrContractInit = cls.env["hr.contract.init"]

        # Every employee always owns a version dated today, so the employee
        # version is backdated to leave today's effective date free for the
        # version created by the test (``hr.version`` has a unique index on
        # employee/effective date).
        cls.eeJohn = cls.HrEmployee.create(
            {"name": "John", "date_version": "2000-01-01"}
        )

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

        contract = self.HrVersion.create(
            {
                "employee_id": self.eeJohn.id,
                "wage": 1.0,
            }
        )
        cInits = self.HrContractInit.search([])
        self.assertEqual(countInits + 2, len(cInits))
        self.assertEqual(psB.id, contract.struct_id.id)
