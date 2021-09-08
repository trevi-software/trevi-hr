# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestCasePublicHoliday(TransactionCase):
    def setUp(self):
        super(TestCasePublicHoliday, self).setUp()

        # -- Models
        self.Users = self.env["res.users"]
        self.Groups = self.env["res.groups"]
        self.HolidayPublic = self.env["hr.holidays.public"]
        self.HolidayPublicLine = self.env["hr.holidays.public.line"]

        # -- Hr Groups
        self.hr_group_user = self.env.ref("hr.group_hr_user")
        self.hr_group_manager = self.env.ref("hr.group_hr_manager")

        # -- Users
        self.hr_user = self.env["res.users"].create(
            {
                "name": "Hr User",
                "login": "hruser",
                "groups_id": [(4, self.hr_group_user.id)],
            }
        )
        self.hr_officer = self.env["res.users"].create(
            {
                "name": "Hr Officer",
                "login": "hrofficer",
                "groups_id": [(4, self.hr_group_manager.id)],
            }
        )

        # -- holiday dates
        self.new_year = datetime.strptime("2021-09-11", "%Y-%m-%d").date()
        self.good_friday = datetime.strptime("2021-04-30", "%Y-%m-%d").date()
        self.ester = datetime.strptime("2021-05-02", "%Y-%m-%d").date()

        # -- Holiday Data
        self.holidays = self.HolidayPublicLine.with_user(self.hr_officer).create(
            [
                {"name": "New Year", "date": self.new_year, "variable": False},
                {"name": "Good Friday", "date": self.good_friday, "variable": False},
                {"name": "Ester", "date": self.ester, "variable": False},
            ]
        )

        self.coptic_holidays = self.HolidayPublic.with_user(self.hr_officer).create(
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

    def test_normal_user_cant_add_public_holidays(self):
        coptic_holidays = self.HolidayPublic.with_user(self.hr_user).browse(
            self.coptic_holidays.id
        )
        _holidays = [(4, holiday.id) for holiday in self.holidays]
        with self.assertRaises(AccessError):
            coptic_holidays.write({"line_ids": _holidays})

    def test_hr_officer_can_manage_public_holidays(self):

        _holidays = [(4, holiday.id) for holiday in self.holidays]

        self.assertEqual(
            self.HolidayPublic.get_holidays_list(self.coptic_holidays.year), []
        )

        self.HolidayPublic.with_user(self.hr_officer).browse(
            self.coptic_holidays.id
        ).write({"line_ids": _holidays})
        holiday_dates = self.HolidayPublic.with_user(self.hr_officer).get_holidays_list(
            self.coptic_holidays.year
        )

        self.assertIn(self.new_year, holiday_dates)
        self.assertIn(self.good_friday, holiday_dates)
        self.assertIn(self.ester, holiday_dates)
