# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestHrContract(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestHrContract, cls).setUpClass()

        cls.HrContract = cls.env["hr.contract"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.hro = new_test_user(
            cls.env,
            login="hro",
            groups="base.group_user,hr.group_hr_user",
            name="HRO",
            email="hro@example.com",
        )
        cls.john = new_test_user(
            cls.env,
            login="john",
            groups="base.group_user",
            name="John",
            email="j@example.com",
        )
        cls.eeJohn = cls.HrEmployee.create({"name": "John", "user_id": cls.john.id})

    def test_view_own_contract(self):
        """An employee can view his/her own contract"""

        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": self.eeJohn.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        try:
            contract.with_user(self.john.id).read([])
        except AccessError:
            self.fail("raised an AccessError Exception")

    def test_create_contract_user_fails(self):
        """Contract creation by regular user fails"""

        with self.assertRaises(AccessError):
            self.HrContract.with_user(self.john.id).create(
                {
                    "name": "CRef",
                    "employee_id": self.eeJohn.id,
                    "date_start": fields.Date.today(),
                    "wage": 1,
                }
            )

    def test_hr_contract_write_user_fails(self):
        """Write access fails"""

        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": self.eeJohn.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        with self.assertRaises(AccessError):
            contract.with_user(self.john.id).wage = 2

    def test_hr_contract_unlink_user_fails(self):
        """Unlink access fails"""

        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": self.eeJohn.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        with self.assertRaises(AccessError):
            contract.with_user(self.john.id).unlink()

    def test_view_contract_officer(self):
        """An HR Officer can view any contract"""

        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": self.eeJohn.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        try:
            contract.with_user(self.hro.id).read([])
        except AccessError:
            self.fail("raised an AccessError Exception")

    def test_create_contract_officer_fails(self):
        """Contract creation by regular user fails"""

        with self.assertRaises(AccessError):
            self.HrContract.with_user(self.hro.id).create(
                {
                    "name": "CRef",
                    "employee_id": self.eeJohn.id,
                    "date_start": fields.Date.today(),
                    "wage": 1,
                }
            )

    def test_hr_contract_write_officer_fails(self):
        """Write access fails"""

        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": self.eeJohn.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        with self.assertRaises(AccessError):
            contract.with_user(self.hro.id).wage = 2

    def test_hr_contract_unlink_officer_fails(self):
        """Unlink access fails"""

        contract = self.HrContract.create(
            {
                "name": "CRef",
                "employee_id": self.eeJohn.id,
                "date_start": fields.Date.today(),
                "wage": 1,
            }
        )
        with self.assertRaises(AccessError):
            contract.with_user(self.hro.id).unlink()
