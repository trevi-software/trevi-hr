# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from psycopg2 import IntegrityError

from odoo.tests import common

CODE = "XXX"


class TestHrLeaveType(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestHrLeaveType, cls).setUpClass()

        cls.HrLeaveType = cls.env["hr.leave.type"]
        cls.company1 = cls.env["res.company"].create({"name": "A company"})
        cls.company2 = cls.env["res.company"].create({"name": "B company"})

    def test_leave_type_is_unique(self):
        """Leave type codes should be unique"""

        self.HrLeaveType.create({"name": "X", "code": CODE})
        with self.assertRaises(IntegrityError):
            self.HrLeaveType.create({"name": "Y", "code": CODE})

    def test_unique_multicompany(self):
        """Multiple companies can have the same code"""

        self.HrLeaveType.with_company(self.company1).create({"name": "X", "code": CODE})
        try:
            self.HrLeaveType.with_company(self.company2).create(
                {"name": "X", "code": CODE}
            )
        except Exception:
            self.assertFail("An unexpected exception was raised")
