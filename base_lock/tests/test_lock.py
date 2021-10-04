# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestLock(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestLock, cls).setUpClass()

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
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        try:
            lk.with_user(self.user.id).read([])
        except AccessError:
            self.fail("raised an AccessError exception")

    def test_user_write_fails(self):
        """Write access fails"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        with self.assertRaises(AccessError):
            lk.with_user(self.user.id).name = "B"

    def test_user_create_fails(self):
        """Create access fails"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
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
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        with self.assertRaises(AccessError):
            lk.with_user(self.user.id).unlink()

    def test_lock_datetime_utc(self):
        """Locking of datetime value"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)

        lk = self.create_lock(start, end, "Africa/Addis_Ababa")

        # just before lock start
        self.assertFalse(lk.is_locked_datetime_utc("2020-12-31 02:59:59"))
        # just after lock end
        self.assertFalse(lk.is_locked_datetime_utc("2021-01-31 21:00:00"))
        # at lock start
        self.assertTrue(lk.is_locked_datetime_utc("2020-12-31 21:00:00"))
        # in the middle of the lock period
        self.assertTrue(lk.is_locked_datetime_utc("2021-01-15 03:00:00"))
        # at lock end
        self.assertTrue(lk.is_locked_datetime_utc("2021-01-31 20:59:59"))

    def test_lock_date_tz(self):
        """Locking of date value with timezone info"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")

        # day before lock start
        self.assertFalse(lk.is_locked_date("2020-12-31", "Africa/Addis_Ababa"))
        # day after lock end
        self.assertFalse(lk.is_locked_date("2021-02-01", "Africa/Addis_Ababa"))
        # day of lock start
        self.assertTrue(lk.is_locked_date("2021-01-01", "Africa/Addis_Ababa"))
        # day of lock end
        self.assertTrue(lk.is_locked_date("2021-01-31", "Africa/Addis_Ababa"))

    def test_lock_date_notz(self):
        """Locking of date value without timezone info"""

        # utc: 2021-01-01 00:00:00 - 2021-01-31 23:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")

        # day before lock start
        self.assertFalse(lk.is_locked_date("2020-12-31"))
        # day after lock end
        self.assertFalse(lk.is_locked_date("2021-02-01"))
        # day of lock start
        self.assertTrue(lk.is_locked_date("2021-01-01"))
        # day of lock end
        self.assertTrue(lk.is_locked_date("2021-01-31"))
