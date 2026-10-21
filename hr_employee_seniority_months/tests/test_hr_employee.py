# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common, tagged
from odoo.tools.float_utils import float_compare, float_is_zero


# These tests build their own records: in Odoo 19 a contract is an
# ``hr.version`` record, and the ``hr_contract`` module no longer exists.
# They must run after all modules are installed, because the versions created
# here carry fields that are only added to ``hr.version`` by modules installed
# alongside this one (``hr_work_entry``, whose ``work_entry_source`` is a
# required field).
@tagged("post_install", "-at_install")
class TestHrEmployeeSeniority(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.HrEmployee = self.env["hr.employee"]
        self.HrVersion = self.env["hr.version"]

    def _create_contract(self, employee, date_start, date_end=False, name="C"):
        """Create the ``hr.version`` that represents a contract."""

        return self.HrVersion.create(
            {
                "name": name,
                "employee_id": employee.id,
                "date_version": date_start,
                "contract_date_start": date_start,
                "contract_date_end": date_end,
                "wage": 1.0,
            }
        )

    def _get_days_in_month(self, d):
        last_date = (
            d
            - timedelta(days=(d.day - 1))
            + relativedelta(months=+1)
            + relativedelta(days=-1)
        )
        return last_date.day

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
        self._create_contract(ee, dStart1, dEnd1, "C1")
        self._create_contract(ee, dStart2, dEnd2, "C2")
        self.assertEqual(
            float_compare(18.0, ee.length_of_service, precision_digits=2), 0
        )

    def test_current_contract_seniority(self):
        """Current contract seniority cutoff is Today"""

        dStart = fields.Date.today() - relativedelta(months=3)
        dEnd = fields.Date.today() + relativedelta(months=12)
        ee = self.HrEmployee.create({"name": "EE 1"})
        self._create_contract(ee, dStart, dEnd)
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
        self._create_contract(ee, dStart1, dEnd1, "C1")
        self._create_contract(ee, dStart2, dEnd2, "C2")

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
        self._create_contract(
            ee, fields.Date.today() + relativedelta(months=3), False, "C"
        )
        self.assertEqual(
            float_compare(0.0, ee.length_of_service, precision_digits=2), 0
        )

    def test_contract_end_in_future(self):
        """Contract with end date in the future returns only until today"""

        ee = self.HrEmployee.create({"name": "EE"})
        contract_start = fields.Date.today() - relativedelta(months=3, days=14)
        self._create_contract(
            ee,
            contract_start,
            fields.Date.today() + relativedelta(months=3),
            "C",
        )
        delta = abs(
            relativedelta(
                contract_start,
                fields.Date.today(),
            )
        )
        next_even_month = contract_start + relativedelta(months=4)
        prev_even_month = contract_start + relativedelta(months=3)
        timedelta_month_days = datetime.combine(
            next_even_month, datetime.min.time()
        ) - datetime.combine(prev_even_month, datetime.min.time())
        total_month_days = timedelta_month_days / timedelta(days=1)
        relative_today_days = relativedelta(prev_even_month, fields.Date.today())
        months = round(
            (
                float(delta.years * 12 + delta.months)
                + abs(relative_today_days.days / total_month_days)
            ),
            2,
        )
        self.assertEqual(
            float_compare(months, ee.length_of_service, precision_digits=1), 0
        )

    def test_version_on_same_contract_is_not_double_counted(self):
        """A new version of the same contract does not add seniority twice

        A wage revision creates a new hr.version that keeps the contract
        dates, so the contract period must only be counted once.
        """

        dStart = fields.Date.today() - relativedelta(months=12)
        dEnd = dStart + relativedelta(months=12)
        ee = self.HrEmployee.create({"name": "EE"})
        self._create_contract(ee, dStart, dEnd, "C")
        self.HrVersion.create(
            {
                "name": "C (revision)",
                "employee_id": ee.id,
                "date_version": dStart + relativedelta(months=6),
                "contract_date_start": dStart,
                "contract_date_end": dEnd,
                "wage": 2.0,
            }
        )
        self.assertEqual(
            float_compare(12.0, ee.length_of_service, precision_digits=2), 0
        )

    def test_no_contract_no_employment_date(self):
        """An employee without a contract has no employment date"""

        ee = self.HrEmployee.create({"name": "EE"})
        self.assertIsNone(ee.get_employment_date())

    def test_get_employment_date(self):
        """An employee with a contract has an employment date"""

        START = "2021-01-01"
        ee = self.HrEmployee.create({"name": "EE"})
        self._create_contract(ee, START)
        start = fields.Date.to_date(START)
        self.assertEqual(ee.get_employment_date(), start)
