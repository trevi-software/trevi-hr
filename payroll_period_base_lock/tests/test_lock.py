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

        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="hel",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
            email="hel@example.com",
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

    def test_pm_write(self):
        """Has write access to lock.lock"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        try:
            lk.with_user(self.userPM.id).name = "B"
        except AccessError:
            self.fail("raised an AccessError exception")

    def test_pm_read(self):
        """Has read access to lock.lock"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        try:
            lk.with_user(self.userPM.id).read([])
        except AccessError:
            self.fail("raised an AccessError exception")

    def test_pm_create(self):
        """Create access"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        try:
            self.Lock.with_user(self.userPM.id).create(
                {
                    "name": "A",
                    "start_time": start,
                    "end_time": end,
                    "tz": "Africa/Addis_Ababa",
                }
            )
        except AccessError:
            self.fail("raised an AccessError exception")

    def test_pm_unlink(self):
        """Unlink access"""

        # utc: 2020-12-31 21:00:00 - 2021-01-31 20:59:59
        start = datetime(2021, 1, 1, 0, 0, 0)
        end = datetime(2021, 1, 31, 23, 59, 59)
        lk = self.create_lock(start, end, "Africa/Addis_Ababa")
        try:
            lk.with_user(self.userPM.id).unlink()
        except AccessError:
            self.fail("raised an AccessError exception")
