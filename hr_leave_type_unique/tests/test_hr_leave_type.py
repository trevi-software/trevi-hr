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
        """Multiple companies may use the same code"""

        # hr.leave.type.company_id lost its default in 19.0 and with_company()
        # only sets the context, so the company has to be passed explicitly;
        # asserting it also proves the two records really are in two different
        # companies (a NULL company never collides in UNIQUE(company_id, code)).
        lt1 = self.HrLeaveType.create(
            {"name": "X", "code": CODE, "company_id": self.company1.id}
        )
        lt2 = self.HrLeaveType.create(
            {"name": "X", "code": CODE, "company_id": self.company2.id}
        )

        self.assertEqual(lt1.company_id, self.company1)
        self.assertEqual(lt2.company_id, self.company2)
        self.assertNotEqual(lt1.company_id, lt2.company_id)
