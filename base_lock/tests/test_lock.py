# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestLock(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Lock = cls.env["base.lock"]

        # normal user
        cls.user = new_test_user(
            cls.env,
            login="reg",
            groups="base.group_user",
            name="Simple employee",
            email="reg@example.com",
        )

    def create_lock(self, start, end, tz):
        return self.Lock.create(
            {
                "name": "A lock",
                "start_time": start,
                "end_time": end,
                "tz": tz,
            }
        )

    def test_user_read(self):
        """Has read access to lock.lock"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)  # noqa: DTZ001
        end = datetime(2021, 1, 31, 23, 59, 59)  # noqa: DTZ001
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        try:
            lk.with_user(self.user.id).read([])
        except AccessError:
            self.fail("raised an AccessError exception")

    def test_user_write_fails(self):
        """Write access fails"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)  # noqa: DTZ001
        end = datetime(2021, 1, 31, 23, 59, 59)  # noqa: DTZ001
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        with self.assertRaises(AccessError):
            lk.with_user(self.user.id).name = "B"

    def test_user_create_fails(self):
        """Create access fails"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)  # noqa: DTZ001
        end = datetime(2021, 1, 31, 23, 59, 59)  # noqa: DTZ001
        with self.assertRaises(AccessError):
            self.Lock.with_user(self.user.id).create(
                {
                    "name": "A",
                    "start_time": start,
                    "end_time": end,
                    "tz": "Africa/Addis_Ababa",
                }
            )

    def test_user_unlink_fails(self):
        """Unlink access fails"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)  # noqa: DTZ001
        end = datetime(2021, 1, 31, 23, 59, 59)  # noqa: DTZ001
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        with self.assertRaises(AccessError):
            lk.with_user(self.user.id).unlink()

    def test_lock_datetime_utc(self):
        """Locking of datetime value"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)  # noqa: DTZ001
        end = datetime(2021, 1, 31, 23, 59, 59)  # noqa: DTZ001

        lk = self.create_lock(start, end, "Africa/Addis_Ababa")

        # just before lock start
        self.assertFalse(lk.is_locked_datetime_utc("2020-12-31 02:59:59"))
        # just after lock end
        self.assertFalse(lk.is_locked_datetime_utc("2021-01-31 21:00:00"))
        # at lock start
        self.assertTrue(lk.is_locked_datetime_utc("2020-12-31 21:00:00"))
        # in the middle of the lock period
        self.assertTrue(lk.is_locked_datetime_utc("2021-01-15 03:00:00"))

    def test_create_with_datetime_strings(self):
        """Datetimes sent as strings are accepted and converted to UTC.

        JSON-RPC payloads (and values taken from ``read()``) carry datetimes as
        strings; the ORM only converts them after ``create()`` overrides have
        run, so the override must normalise them itself.
        """

        lk = self.Lock.create(
            {
                "name": "A lock",
                "start_time": "2021-01-01 00:00:00",
                "end_time": "2021-01-31 23:59:59",
                "tz": "Africa/Addis_Ababa",
            }
        )
        self.assertTrue(lk.exists())
        # Africa/Addis_Ababa is UTC+3 all year round
        self.assertEqual(lk.start_time, datetime(2020, 12, 31, 21, 0, 0))  # noqa: DTZ001
        self.assertEqual(lk.end_time, datetime(2021, 1, 31, 20, 59, 59))  # noqa: DTZ001
