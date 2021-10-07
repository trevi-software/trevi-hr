# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common
from odoo.tools.float_utils import float_compare, float_is_zero


class TestHrEmployeeSeniority(common.TransactionCase):
    def setUp(self):
        super(TestHrEmployeeSeniority, self).setUp()

        self.HrEmployee = self.env["hr.employee"]
        self.HrContract = self.env["hr.contract"]

    def test_no_contract(self):
        """Seniority of employee with no contracts is zero"""

        ee = self.HrEmployee.create({"name": "EE 1"})
        self.assertTrue(float_is_zero(ee.length_of_service, precision_digits=2))

    def test_consecutive_contracts_are_additive(self):
        """Seniority of employee with multiple consecutive contracts is additive"""

        dStart1 = fields.Date.today() - relativedelta(months=24)
        dEnd1 = dStart1 + relativedelta(months=12)
        dStart2 = dEnd1 + relativedelta(days=1)
        dEnd2 = dStart2 + relativedelta(months=6)
        ee = self.HrEmployee.create({"name": "EE 1"})
        self.HrContract.create(
            {
                "name": "C1",
                "employee_id": ee.id,
                "wage": 1.0,
                "date_start": dStart1,
                "date_end": dEnd1,
            }
        )
        self.HrContract.create(
            {
                "name": "C2",
                "employee_id": ee.id,
                "wage": 1.0,
                "date_start": dStart2,
                "date_end": dEnd2,
            }
        )
        self.assertEqual(
            float_compare(18.0, ee.length_of_service, precision_digits=2), 0
        )

    def test_current_contract_seniority(self):
        """Current contract seniority cutoff is Today"""

        dStart = fields.Date.today() - relativedelta(months=3)
        dEnd = fields.Date.today() + relativedelta(months=12)
        ee = self.HrEmployee.create({"name": "EE 1"})
        self.HrContract.create(
            {
                "name": "C",
                "employee_id": ee.id,
                "wage": 1.0,
                "date_start": dStart,
                "date_end": dEnd,
            }
        )
        self.assertEqual(
            float_compare(3.0, ee.length_of_service, precision_digits=2), 0
        )

    def test_gap_between_contracts(self):
        """Gaps between contracts are not counted in seniority"""

        dStart1 = fields.Date.today() - relativedelta(months=24)
        dEnd1 = dStart1 + relativedelta(months=9)
        dStart2 = fields.Date.today() - relativedelta(months=7)
        dEnd2 = dStart2 + relativedelta(months=2)
        ee = self.HrEmployee.create({"name": "EE"})
        self.HrContract.create(
            {
                "name": "C1",
                "employee_id": ee.id,
                "wage": 1.0,
                "date_start": dStart1,
                "date_end": dEnd1,
            }
        )
        self.HrContract.create(
            {
                "name": "C2",
                "employee_id": ee.id,
                "wage": 1.0,
                "date_start": dStart2,
                "date_end": dEnd2,
            }
        )

        self.assertEqual(
            float_compare(
                8.0, relativedelta(dStart2, dEnd1).months, precision_digits=2
            ),
            0,
        )
        self.assertEqual(
            float_compare(11.0, ee.length_of_service, precision_digits=2), 0
        )

    def test_contract_in_future_is_zero(self):
        """Contract with dates in the future returns a zero result"""

        ee = self.HrEmployee.create({"name": "EE"})
        self.HrContract.create(
            {
                "name": "C",
                "employee_id": ee.id,
                "wage": 1.0,
                "date_start": fields.Date.today() + relativedelta(months=3),
            }
        )
        self.assertEqual(
            float_compare(0.0, ee.length_of_service, precision_digits=2), 0
        )

    def test_no_contract_no_employment_date(self):
        """An employee without a contract has no employment date"""

        ee = self.HrEmployee.create({"name": "EE"})
        self.assertIsNone(ee.get_employment_date())

    def test_get_employment_date(self):
        """An employee with a contract has an employment date"""

        START = "2021-01-01"
        ee = self.HrEmployee.create({"name": "EE"})
        self.HrContract.create(
            {
                "name": "C",
                "employee_id": ee.id,
                "wage": 1.0,
                "date_start": START,
            }
        )
        start = fields.Date.to_date(START)
        self.assertEqual(ee.get_employment_date(), start)
