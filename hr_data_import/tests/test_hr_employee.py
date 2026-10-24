# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common
from odoo.tools.float_utils import float_compare


class TestHrEmployeeSeniority(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.HrEmployee = self.env["hr.employee"]

    def test_hire_date(self):
        """Seniority is counted from the hire date, not from the contract."""
        dHire = fields.Date.today() - relativedelta(months=12)
        dStart = fields.Date.today() - relativedelta(months=3)
        ee = self.HrEmployee.create({"name": "EE 1"})
        # In Odoo 19 a contract is an ``hr.version``: the employee is created
        # with one version dated today, which becomes the contract here.
        ee.version_id.write(
            {
                "date_version": dStart,
                "contract_date_start": dStart,
                "wage": 1.0,
            }
        )
        ee.hire_date = dHire
        self.assertEqual(
            float_compare(12.0, ee.length_of_service, precision_digits=2),
            0,
            "Seniority is based on hire date, not contract",
        )
