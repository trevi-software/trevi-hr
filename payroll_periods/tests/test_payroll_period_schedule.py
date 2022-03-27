# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

from odoo.tests import common, new_test_user

from ..models.hr_payroll_period_schedule import add_months


class TestSchedule(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestSchedule, cls).setUpClass()

        cls.Period = cls.env["hr.payroll.period"]
        cls.Schedule = cls.env["hr.payroll.period.schedule"]
        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="hel",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
            email="ric@example.com",
        )

    def create_payroll_schedule(self, stype=False, initial_date=False):
        return self.Schedule.create(
            {
                "name": "PPS",
                "tz": "Africa/Addis_Ababa",
                "type": stype,
                "initial_period_date": initial_date,
            }
        )

    def apply_create_cron(self):
        self.env.ref(
            "payroll_periods.hr_payroll_period_create_cron"
        ).method_direct_trigger()

    def test_annual_period_no(self):
        """There are 12 annual periods for monthly schedule"""

        pps = self.create_payroll_schedule("monthly", date.today())
        self.assertEqual(12, pps.annual_pay_periods)

    def test_initial_periods_creation_button(self):
        """One period is created from initial start date"""

        pps = self.create_payroll_schedule("monthly", date(2021, 1, 1))
        pps.button_add_pay_periods()

        listPP = self.Period.search([])
        self.assertEqual(1, len(listPP))
        self.assertEqual("Pay Period 2021/January", listPP[0].name)
        # utc is -3:00 hours
        self.assertEqual(datetime(2020, 12, 31, 21, 0, 0), listPP[0].date_start)
        self.assertEqual(datetime(2021, 1, 31, 20, 59, 59), listPP[0].date_end)

    def convert_local_to_utc(self, tz_str, lyear, lmonth, lday, lh=0, lm=0, ls=0):

        ltz = timezone(tz_str)
        ltzdtToday = ltz.localize(
            datetime(lyear, lmonth, lday, lh, lm, ls), is_dst=None
        )
        utcdtToday = ltzdtToday.astimezone(utc)
        return utcdtToday.replace(tzinfo=None)

    def test_initial_periods_creation_cron(self):
        """Three periods are created from initial start date"""

        today = date.today()
        today = date(today.year, today.month, 1)

        # Africa/Addis_Ababa is +3:00 UTC (00:00:00 -> 21:00:00)
        #
        mo1 = self.convert_local_to_utc(
            "Africa/Addis_Ababa", today.year, today.month, 1
        )
        mo1end = add_months(today, 1) - relativedelta(days=1)
        mo1end = self.convert_local_to_utc(
            "Africa/Addis_Ababa", mo1end.year, mo1end.month, mo1end.day, 23, 59, 59
        )

        mo2 = add_months(today, 1)
        mo2 = self.convert_local_to_utc("Africa/Addis_Ababa", mo2.year, mo2.month, 1)

        mo2end = add_months(today, 2) - relativedelta(days=1)
        mo2end = self.convert_local_to_utc(
            "Africa/Addis_Ababa", mo2end.year, mo2end.month, mo2end.day, 23, 59, 59
        )

        mo3 = add_months(today, 2)
        mo3 = self.convert_local_to_utc("Africa/Addis_Ababa", mo3.year, mo3.month, 1)

        mo3end = add_months(today, 3) - relativedelta(days=1)
        mo3end = self.convert_local_to_utc(
            "Africa/Addis_Ababa", mo3end.year, mo3end.month, mo3end.day, 23, 59, 59
        )

        # Create schedule and run cron to create the first periods
        self.create_payroll_schedule("monthly", today)
        self.apply_create_cron()

        listPP = self.Period.search([])
        self.assertEqual(3, len(listPP))

        self.assertEqual(mo1, listPP[0].date_start)
        self.assertEqual(mo1end, listPP[0].date_end)
        self.assertEqual(mo2, listPP[1].date_start)
        self.assertEqual(mo2end, listPP[1].date_end)
        self.assertEqual(mo3, listPP[2].date_start)
        self.assertEqual(mo3end, listPP[2].date_end)
