# Copyright (C) 2021 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import common


class TestAccrual(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccrual, cls).setUpClass()

        cls.Accrual = cls.env["hr.accrual"]
        cls.Allocation = cls.env["hr.leave.allocation"]
        cls.eeJohn = cls.env["hr.employee"].create({"name": "EE John"})

        # Make sure we have the rights to create, validate and delete the
        # leaves, leave types and allocations
        LeaveType = cls.env["hr.leave.type"].with_context(tracking_disable=True)

        cls.accrual_type = LeaveType.create(
            {
                "name": "accrual",
                "allocation_type": "fixed",
                "validity_start": False,
            }
        )

    def test_accrual_deposit_and_balance(self):
        """The balance should be the same amount deposited"""

        accrual = self.Accrual.create({"name": "A"})
        accrual.deposit(self.eeJohn.id, 100, fields.Date.today(), "manual accrual")
        self.assertEqual(100, accrual.get_balance(self.eeJohn.id))

    def test_create_leave_allocation(self):
        """A deposit should create a corresponding leave allocation"""

        accrual = self.Accrual.create(
            {"name": "A", "holiday_status_id": self.accrual_type.id}
        )
        accrual.deposit(self.eeJohn.id, 2.0, fields.Date.today(), "manual accrual")

        allocs = self.Allocation.search([("name", "=", "manual accrual")])
        self.assertEqual(1, len(allocs))
        self.assertTrue(allocs[0].from_accrual)
        self.assertEqual(allocs[0].allocation_type, "regular")
        self.assertEqual(
            0,
            fields.Float.compare(
                allocs[0].number_of_days_display, 2.0, precision_digits=1
            ),
        )
        self.assertEqual(
            0, fields.Float.compare(allocs[0].number_of_days, 2.0, precision_digits=1)
        )
