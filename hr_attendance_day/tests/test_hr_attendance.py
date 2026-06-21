# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from odoo.tests import common


class TestHrAttendance(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Attendance = cls.env["hr.attendance"]

        # Africa/Accra is UTC + 0:00
        cls.john = cls.env["hr.employee"].create({"name": "John", "tz": "Africa/Accra"})

        # Africa/Addis_Ababa is UTC + 3:00
        cls.sally = cls.env["hr.employee"].create(
            {"name": "Sally", "tz": "Africa/Addis_Ababa"}
        )

    def test_utc_and_tz_match(self):

        check_in = datetime(2022, 4, 1, 23, 59, 59)
        check_out = datetime(2022, 4, 2, 8, 0)
        att = self.Attendance.create(
            {
                "employee_id": self.john.id,
                "check_in": check_in,
                "check_out": check_out,
            }
        )

        self.assertEqual(
            att.day,
            date(2022, 4, 1),
            "Timezone with zero offset (1) from UTC has correct date",
        )

        check_in = datetime(2022, 4, 3, 0, 0, 0)
        check_out = datetime(2022, 4, 3, 8, 0)
        att = self.Attendance.create(
            {
                "employee_id": self.john.id,
                "check_in": check_in,
                "check_out": check_out,
            }
        )

        self.assertEqual(
            att.day,
            date(2022, 4, 3),
            "Timezone with zero offset (2) from UTC has correct date",
        )

    def test_utc_and_tz_mismatch(self):

        att = self.Attendance.create(
            {
                "employee_id": self.sally.id,
                "check_in": datetime(2022, 4, 1, 21, 0),
                "check_out": datetime(2022, 4, 2, 5, 0),
            }
        )

        self.assertEqual(
            att.day,
            date(2022, 4, 2),
            "Timezone with +3:00 offset (1) from UTC has correct date",
        )

    def test_update(self):

        att = self.Attendance.create(
            {
                "employee_id": self.sally.id,
                "check_in": datetime(2022, 4, 1, 21, 0),
                "check_out": datetime(2022, 4, 2, 5, 0),
            }
        )

        self.assertEqual(
            att.day,
            date(2022, 4, 2),
            "Timezone with +3:00 offset (1) from UTC has correct date",
        )

        att.check_in = datetime(2022, 4, 1, 20, 59, 59)
        self.assertEqual(
            att.day,
            date(2022, 4, 1),
            "Changing check-in backwards by 1 second from midnight (in local tz) "
            "changes the day",
        )
