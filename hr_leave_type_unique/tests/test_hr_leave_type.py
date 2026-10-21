# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from psycopg2 import IntegrityError

from odoo.tests import common
from odoo.tools import mute_logger

CODE = "XXX"


class TestHrLeaveType(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.HrLeaveType = cls.env["hr.leave.type"]
        cls.company1 = cls.env["res.company"].create({"name": "A company"})
        cls.company2 = cls.env["res.company"].create({"name": "B company"})

    def test_leave_type_is_unique(self):
        """Leave type codes should be unique"""

        # Since 19.0, hr.leave.type.company_id has no default (it used to
        # default to the current company), and a UNIQUE(company_id, code)
        # index does not apply to NULL companies. Set it explicitly so the
        # constraint is actually exercised.
        self.HrLeaveType.create(
            {"name": "X", "code": CODE, "company_id": self.env.company.id}
        )
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.HrLeaveType.create(
                {"name": "Y", "code": CODE, "company_id": self.env.company.id}
            )

    def test_unique_multicompany(self):
        """Multiple companies can have the same code"""

        self.HrLeaveType.with_company(self.company1).create({"name": "X", "code": CODE})
        try:
            self.HrLeaveType.with_company(self.company2).create(
                {"name": "X", "code": CODE}
            )
        except Exception:
            self.assertFail("An unexpected exception was raised")
