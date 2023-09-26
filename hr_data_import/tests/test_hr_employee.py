# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common
from odoo.tools.float_utils import float_compare


class TestHrEmployeeSeniority(common.TransactionCase):
    def setUp(self):
        super(TestHrEmployeeSeniority, self).setUp()

        self.HrEmployee = self.env["hr.employee"]
        self.HrContract = self.env["hr.contract"]

    def test_hire_date(self):

        dHire = fields.Date.today() - relativedelta(months=12)
        dStart = fields.Date.today() - relativedelta(months=3)
        ee = self.HrEmployee.create({"name": "EE 1"})
        ee.hire_date = dHire
        self.HrContract.create(
            {
                "name": "C",
                "employee_id": ee.id,
                "wage": 1.0,
                "date_start": dStart,
            }
        )
        self.assertEqual(
            float_compare(12.0, ee.length_of_service, precision_digits=2),
            0,
            "Seniority is based on hire date, not contract",
        )
