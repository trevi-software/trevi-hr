# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests import common


class TestContract(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestContract, cls).setUpClass()

        cls.IrConfig = cls.env["ir.config_parameter"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.employee = cls.HrEmployee.create({"name": "John"})

    def create_contract(self, state, kanban_state, start, end=None):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": self.employee.id,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "date_end": end,
            }
        )

    def test_no_concurrent_contracts(self):
        """If concurrent contracts aren't enabled creating a
        second contract fails"""

        self.assertFalse(
            self.IrConfig.get_param("hr_contract_statuss.concurrent_contracts", False)
        )
        start = datetime.strptime("2015-11-01", "%Y-%m-%d").date()
        end = datetime.strptime("2015-11-30", "%Y-%m-%d").date()
        self.create_contract("open", "normal", start, end)

        # Incoming contract
        with self.assertRaises(
            ValidationError,
            msg="It should not create two contract in state open or incoming",
        ):
            start = datetime.strptime("2015-11-15", "%Y-%m-%d").date()
            end = datetime.strptime("2015-12-30", "%Y-%m-%d").date()
            self.create_contract("draft", "done", start, end)

    def test_concurrent_contracts(self):
        """If concurrent contracts are enabled creating more than
        one open contract suceeds"""

        self.IrConfig.sudo().set_param("hr_contract_statuss.concurrent_contracts", True)
        self.assertTrue(
            self.IrConfig.get_param("hr_contract_statuss.concurrent_contracts", False)
        )
        start = datetime.strptime("2015-11-01", "%Y-%m-%d").date()
        end = datetime.strptime("2015-11-30", "%Y-%m-%d").date()
        self.create_contract("open", "normal", start, end)

        # Incoming contract
        try:
            start = datetime.strptime("2015-11-15", "%Y-%m-%d").date()
            end = datetime.strptime("2015-12-30", "%Y-%m-%d").date()
            self.create_contract("draft", "done", start, end)
        except ValidationError:
            self.fail("Unexpected ValidationError exception")
