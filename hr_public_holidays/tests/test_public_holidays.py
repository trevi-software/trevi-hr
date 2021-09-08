##############################################################################
#
#    Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestCasePublicHoliday(TransactionCase):
    def setUp(self):
        super(TestCasePublicHoliday, self).setUp()

        # -- Models
        self.HolidayPublic = self.env["hr.holidays.public"]
        self.HolidayPublicLine = self.env["hr.holidays.public.line"]

        # -- holiday dates
        self.new_year = datetime.strptime("2021-09-11", "%Y-%m-%d").date()
        self.good_friday = datetime.strptime("2021-04-30", "%Y-%m-%d").date()
        self.ester = datetime.strptime("2021-05-02", "%Y-%m-%d").date()

        # -- Holiday Data
        self.holidays = self.HolidayPublicLine.create(
            [
                {"name": "New Year", "date": self.new_year, "variable": False},
                {"name": "Good Friday", "date": self.good_friday, "variable": False},
                {"name": "Ester", "date": self.ester, "variable": False},
            ]
        )

        self.coptic_holidays = self.HolidayPublic.create(
            {"year": "2021", "line_ids": False}
        )

    def add_holiday_to_public_holidays(self, holidays):
        _h = [(4, h.id) for h in holidays]
        return self.coptic_holidays.write({"line_ids": _h})

    def test_check_date_is_public_holiday(self):
        self.add_holiday_to_public_holidays(self.holidays)

        day_after_new_year = self.new_year + timedelta(days=1)
        day_after_good_friday = self.good_friday + timedelta(days=1)
        day_after_ester = self.ester + timedelta(days=1)

        self.assertTrue(self.coptic_holidays.is_public_holiday(self.new_year))
        self.assertTrue(self.coptic_holidays.is_public_holiday(self.good_friday))
        self.assertTrue(self.coptic_holidays.is_public_holiday(self.ester))

        self.assertFalse(self.coptic_holidays.is_public_holiday(day_after_new_year))
        self.assertFalse(self.coptic_holidays.is_public_holiday(day_after_good_friday))
        self.assertFalse(self.coptic_holidays.is_public_holiday(day_after_ester))

    def test_get_holidays_list(self):
        self.add_holiday_to_public_holidays(self.holidays)

        holiday_list = self.HolidayPublic.get_holidays_list(self.coptic_holidays.year)

        self.assertIn(self.new_year, holiday_list)
        self.assertIn(self.good_friday, holiday_list)
        self.assertIn(self.ester, holiday_list)
