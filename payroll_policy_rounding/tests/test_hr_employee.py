# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import fields

from . import common


class TestHrEmployee(common.TestPolicyCommon):
    def test_create_checkin(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "down", "round_interval": 5},
            ),
        ]
        self.setup_pg(line_ids)
        self.test_employee.attendance_state = "checked_out"

        # Punch in
        clock_in, check_in = self.set_in_times("8:33", "08:30")
        now = clock_in
        with patch.object(fields.Datetime, "now", lambda *args, **kwargs: now):
            action = self.test_employee._attendance_action("foo")
        self.assertEqual(
            action["action"]["attendance"]["check_in"],
            check_in,
            "The check-in time is rounded DOWN by 5 minutes",
        )
        self.assertEqual(
            action["action"]["attendance"]["clock_in"],
            clock_in,
            "The clock-in time contains the original time",
        )

    def test_write_check_out(self):

        line_ids = [
            (0, 0, {"attendance_type": "out", "round_type": "up", "round_interval": 5}),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "16:51", "16:55")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
            }
        )
        self.test_employee.attendance_state = "checked_in"
        now = clock_out
        with patch.object(fields.Datetime, "now", lambda *args, **kwargs: now):
            action = self.test_employee._attendance_action("foo")
        self.assertEqual(
            action["action"]["attendance"]["check_out"],
            check_out,
            "The check-out time is rounded UP by 5 minutes",
        )
        self.assertEqual(
            att.clock_out,
            action["action"]["attendance"]["clock_out"],
            "The clock-out time contains the original time",
        )
