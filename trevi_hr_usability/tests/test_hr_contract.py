# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestHrContract(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # ``hr.contract`` was merged into ``hr`` and renamed ``hr.version``.
        cls.HrVersion = cls.env["hr.version"]
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
        # Dated in the past so that the contract versions created by the tests
        # do not clash with the (employee_id, date_version) unique index.
        cls.eeJohn = cls.HrEmployee.create(
            {
                "name": "John",
                "user_id": cls.john.id,
                "date_version": "2020-01-01",
            }
        )

    def _get_contract_vals(self):
        return {
            "name": "CRef",
            "employee_id": self.eeJohn.id,
            "date_version": fields.Date.today(),
            "contract_date_start": fields.Date.today(),
            "wage": 1,
        }

    def test_view_own_contract(self):
        """An employee can view his/her own contract"""

        contract = self.HrVersion.create(self._get_contract_vals())
        # Since 19.0 several hr.version fields carry field-level groups
        # (date_version is hr_user-only, wage/contract_date_start are
        # hr_manager-only), so a plain employee can read the record but not
        # those fields.  Read the fields an employee is allowed to see.
        try:
            contract.with_user(self.john.id).read(["name", "employee_id"])
        except AccessError:
            self.fail("raised an AccessError Exception")

    def test_create_contract_user_fails(self):
        """Contract creation by regular user fails"""

        with self.assertRaises(AccessError):
            self.HrVersion.with_user(self.john.id).create(self._get_contract_vals())

    def test_hr_contract_write_user_fails(self):
        """Write access fails"""

        contract = self.HrVersion.create(self._get_contract_vals())
        with self.assertRaises(AccessError):
            contract.with_user(self.john.id).wage = 2

    def test_hr_contract_unlink_user_fails(self):
        """Unlink access fails"""

        contract = self.HrVersion.create(self._get_contract_vals())
        with self.assertRaises(AccessError):
            contract.with_user(self.john.id).unlink()

    def test_view_contract_officer(self):
        """An HR Officer can view any contract"""

        contract = self.HrVersion.create(self._get_contract_vals())
        try:
            contract.with_user(self.hro.id).read([])
        except AccessError:
            self.fail("raised an AccessError Exception")

    # In Odoo 18 the ``hr_contract`` ACLs only granted create/write/unlink to
    # the (removed) contract manager group, so an HR officer could not manage
    # contracts.  In Odoo 19 ``hr.group_hr_user`` owns ``hr.version``
    # (access rights 1,1,1,1), so an HR officer legitimately can - except for
    # the fields that 19.0 restricts to ``hr.group_hr_manager``
    # (``wage``, ``contract_date_start``), which are exercised below.
    def test_create_contract_officer(self):
        """An HR Officer can create a contract"""

        vals = self._get_contract_vals()
        for manager_only in ("wage", "contract_date_start"):
            vals.pop(manager_only)
        contract = self.HrVersion.with_user(self.hro.id).create(vals)
        self.assertTrue(contract.exists())

    def test_hr_contract_write_officer(self):
        """An HR Officer can write on a contract"""

        contract = self.HrVersion.create(self._get_contract_vals())
        contract.with_user(self.hro.id).name = "CRef2"
        self.assertEqual(contract.name, "CRef2")

    def test_manager_only_fields_fail_for_officer(self):
        """Fields restricted to hr.group_hr_manager are refused to an officer"""

        contract = self.HrVersion.create(self._get_contract_vals())
        with self.assertRaises(AccessError):
            contract.with_user(self.hro.id).wage = 2

    def test_hr_contract_unlink_officer(self):
        """An HR Officer can unlink a contract"""

        contract = self.HrVersion.create(self._get_contract_vals())
        contract.with_user(self.hro.id).unlink()
        self.assertFalse(contract.exists())
