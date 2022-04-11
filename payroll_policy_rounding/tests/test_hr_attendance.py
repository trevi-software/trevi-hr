# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from . import common


class TestHrAttendance(common.TestPolicyCommon):
    def test_create_no_contract(self):

        ee = self.HrEmployee.create({"name": "John"})

        att = self.HrAttendance.create(
            {
                "employee_id": ee.id,
                "clock_in": datetime.combine(
                    date.today(), datetime.strptime("800", "%H%M").time()
                ),
            }
        )
        self.assertEqual(
            att.clock_in,
            datetime.combine(date.today(), datetime.strptime("800", "%H%M").time()),
            "Without a contract the check_in time is the clock time",
        )
        self.assertEqual(
            att.clock_in,
            att.check_in,
            "The check_in time and the clock time are the same",
        )

    def test_create_no_policy(self):

        pg = self.PolicyGroup.create(
            {
                "name": "PGroup",
            }
        )

        start = date.today() - timedelta(days=1)
        ee = self.HrEmployee.create({"name": "John"})
        cc = self.create_contract(ee.id, start=start)
        cc.policy_group_id = pg
        self.apply_contract_cron()

        att = self.HrAttendance.create(
            {
                "employee_id": ee.id,
                "clock_in": datetime.combine(
                    date.today(), datetime.strptime("800", "%H%M").time()
                ),
            }
        )
        self.assertEqual(
            att.check_in,
            datetime.combine(date.today(), datetime.strptime("800", "%H%M").time()),
            "Without a rounding policy the check_in time is the clock time",
        )
        self.assertEqual(
            att.clock_in,
            att.check_in,
            "The check_in time and the clock time are the same",
        )

    def test_create_exact_match(self):

        p = self.Policy.create(
            {
                "name": "P1",
                "date": date.today(),
                "tz": "UTC",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "attendance_type": "in",
                            "round_type": "down",
                            "round_interval": 5,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attendance_type": "out",
                            "round_type": "up",
                            "round_interval": 5,
                        },
                    ),
                ],
            }
        )
        pg = self.PolicyGroup.create(
            {
                "name": "PGroup",
                "rounding_policy_ids": [(6, 0, [p.id])],
            }
        )
        self.test_contract.policy_group_id = pg

        self.assertGreater(
            len(self.test_employee.resource_id.scheduled_shift_ids),
            0,
            "Shifts have been created on contract creation",
        )

        shift = self.test_employee.resource_id.scheduled_shift_ids.filtered(
            lambda s: s.dayofweek == str(date.today().weekday())
        )

        # Punch in
        clock_in = self.localize_dt(
            self.make_datetime(date.today(), "08:00"),
            self.test_employee.resource_id.tz,
            reverse=True,
        )
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in,
            shift[0].datetime_start,
            "The attendance and schedule start times match",
        )
        self.assertEqual(att.check_in, clock_in, "The check-in time is an exact match")
        self.assertEqual(
            att.check_in,
            att.clock_in,
            "The check-in and clock-in times are an exact match",
        )

        # Punch out
        clock_out = self.localize_dt(
            self.make_datetime(date.today(), "12:00"),
            self.test_employee.resource_id.tz,
            reverse=True,
        )
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, clock_out, "The check-out time is an exact match"
        )
        self.assertEqual(
            att.check_out,
            att.clock_out,
            "The check-out and clock-out times are an exact match",
        )

    def test_create_in_multi_shift(self):

        # See if we pick up the correct shift when multiple shifts are
        # available in the same day
        #

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "down", "round_interval": 5},
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("13:33", "13:30")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in,
            check_in,
            "The check-in is from the correct shift and rounded DOWN by 5 minutes",
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_in_round_down(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "down", "round_interval": 5},
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("8:33", "08:30")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in, check_in, "The check-in time is rounded DOWN by 5 minutes"
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_in_round_up(self):

        line_ids = [
            (0, 0, {"attendance_type": "in", "round_type": "up", "round_interval": 5}),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("8:33", "8:35")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in, check_in, "The check-in time is rounded UP by 5 minutes"
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_in_round_avg1(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "avg", "round_interval": 15},
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("8:38", "8:45")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in, check_in, "The check-in time is rounded UP by 15 minutes"
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_in_round_avg2(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "avg", "round_interval": 15},
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("8:37", "8:30")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in, check_in, "The check-in time is rounded DOWN by 15 minutes"
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_early_in_round_down(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "down", "round_interval": 5},
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("07:59", "7:55")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in, check_in, "The check-in time is rounded DOWN by 5 minutes"
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_early_in_round_up(self):

        line_ids = [
            (0, 0, {"attendance_type": "in", "round_type": "up", "round_interval": 5}),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("07:55", "7:55")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in,
            check_in,
            "The check-in time is NOT rounded because it matches the interval",
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_early_in_round_avg1(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "avg", "round_interval": 15},
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("07:38", "7:45")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in, check_in, "The check-in time is rounded UP by 15 minutes"
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_early_in_round_avg2(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "avg", "round_interval": 15},
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("07:37", "7:30")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in, check_in, "The check-in time is rounded DOWN by 15 minutes"
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_out_round_down(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "out", "round_type": "down", "round_interval": 5},
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "17:33", "17:30")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is rounded DOWN by 5 minutes"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_out_round_up(self):

        line_ids = [
            (0, 0, {"attendance_type": "out", "round_type": "up", "round_interval": 5}),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "17:33", "17:35")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is rounded UP by 5 minutes"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_out_round_avg1(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "out", "round_type": "avg", "round_interval": 15},
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "17:38", "17:45")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is rounded UP by 15 minutes"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_out_round_avg2(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "out", "round_type": "avg", "round_interval": 15},
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "17:37", "17:30")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is rounded DOWN by 15 minutes"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_early_out_round_down(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "out", "round_type": "down", "round_interval": 5},
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "16:59", "16:55")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is rounded DOWN by 5 minutes"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_early_out_round_up(self):

        line_ids = [
            (0, 0, {"attendance_type": "out", "round_type": "up", "round_interval": 5}),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "16:51", "16:55")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is rounded UP by 5 minutes"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_early_out_round_avg1(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "out", "round_type": "avg", "round_interval": 15},
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "16:38", "16:45")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is rounded UP by 15 minutes"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_early_out_round_avg2(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "out", "round_type": "avg", "round_interval": 15},
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "16:37", "16:30")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is rounded DOWN by 15 minutes"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_preauth_ot_in(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "in",
                    "round_type": "avg",
                    "round_interval": 15,
                    "preauth_ot": True,
                },
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("7:38", "8:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in, check_in, "The check-in time is the scheduled time"
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_preauth_ot_out(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "out",
                    "round_type": "up",
                    "round_interval": 5,
                    "preauth_ot": True,
                },
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("13:00", "17:33", "17:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out, check_out, "The check-out time is the scheduled time"
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_in_grace(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "in",
                    "round_type": "up",
                    "round_interval": 15,
                    "grace": 10,
                },
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("8:07", "8:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in,
            check_in,
            "The clock-in is in grace period so check-in time is actual start time",
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )

    def test_create_early_out_grace_period(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "out",
                    "round_type": "down",
                    "round_interval": 10,
                    "grace": 5,
                },
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "16:55", "17:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertEqual(
            att.check_out,
            check_out,
            "The clock-in is within grace period so check-out time is schedule time",
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_attach_schedule_sign_in(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "in",
                    "round_type": "up",
                    "round_interval": 15,
                    "grace": 10,
                },
            ),
        ]
        tz = self.test_employee.resource_id.tz
        self.setup_pg(line_ids, tz)

        # Punch in
        clock_in, _check_in = self.set_in_times("8:00", "8:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertTrue(att.schedule_shift_id, "The attendance has a related schedule")
        self.assertEqual(
            int(att.schedule_shift_id.dayofweek),
            att.check_in.weekday(),
            "The schedule and the attendance are for the same day",
        )
        self.assertEqual(
            att.schedule_shift_id.datetime_start,
            att.check_in,
            "The schedule and the attendance have the same time",
        )

    def test_attach_schedule_sign_out(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "out",
                    "round_type": "down",
                    "round_interval": 10,
                    "grace": 5,
                },
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, _check_out = self.set_out_times("12:00", "17:00", "17:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
                "clock_out": clock_out,
            }
        )
        self.assertTrue(att.schedule_shift_id, "The attendance has a related schedule")
        self.assertEqual(
            int(att.schedule_shift_id.dayofweek),
            att.check_in.weekday(),
            "The schedule and the attendance are for the same day",
        )
        self.assertEqual(
            att.schedule_shift_id.datetime_end,
            att.check_out,
            "The schedule and the attendance have the same time",
        )

    def test_attach_schedule_sign_out2(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "out",
                    "round_type": "down",
                    "round_interval": 10,
                    "grace": 5,
                },
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, _check_out = self.set_out_times("12:00", "17:00", "17:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
            }
        )
        self.assertFalse(
            att.schedule_shift_id, "The attendance does NOT have a related schedule"
        )

        att.clock_out = clock_out
        self.assertTrue(att.schedule_shift_id, "The attendance has a related schedule")
        self.assertEqual(
            int(att.schedule_shift_id.dayofweek),
            att.check_in.weekday(),
            "The schedule and the attendance are for the same day",
        )
        self.assertEqual(
            att.schedule_shift_id.datetime_end,
            att.check_out,
            "The schedule and the attendance have the same time",
        )

    def test_write_in_grace(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "in",
                    "round_type": "up",
                    "round_interval": 15,
                    "grace": 10,
                },
            ),
        ]
        self.setup_pg(line_ids)

        # Punch in
        clock_in, check_in = self.set_in_times("8:07", "8:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in,
            check_in,
            "The clock-in is in grace period so check-in time is actual start time",
        )

        clock_in2, _check_in2 = self.set_in_times("8:09", "8:00")
        att.clock_in = clock_in2
        self.assertEqual(
            att.check_in,
            check_in,
            "The clock-in is in grace period so check-in time hasn't changed",
        )
        self.assertEqual(
            att.clock_in, clock_in2, "The clock-in time contains the original time"
        )

    def test_write_early_out_grace_period(self):

        line_ids = [
            (
                0,
                0,
                {
                    "attendance_type": "out",
                    "round_type": "down",
                    "round_interval": 10,
                    "grace": 5,
                },
            ),
        ]
        self.setup_pg(line_ids)

        check_in, clock_out, check_out = self.set_out_times("12:00", "16:55", "17:00")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "check_in": check_in,
            }
        )
        att.clock_out = clock_out
        self.assertEqual(
            att.check_out,
            check_out,
            "The clock-in is within grace period so check-out time is schedule time",
        )
        self.assertEqual(
            att.clock_out, clock_out, "The clock-out time contains the original time"
        )

    def test_create_no_shifts(self):

        line_ids = [
            (
                0,
                0,
                {"attendance_type": "in", "round_type": "down", "round_interval": 5},
            ),
        ]
        self.setup_pg(line_ids)
        self.test_employee.resource_id.scheduled_shift_ids.unlink()

        # Punch in
        clock_in, _check_in = self.set_in_times("13:33", "13:30")
        att = self.HrAttendance.create(
            {
                "employee_id": self.test_employee.id,
                "clock_in": clock_in,
            }
        )
        self.assertEqual(
            att.check_in,
            clock_in,
            "The check-in is the clock-in time",
        )
        self.assertEqual(
            att.clock_in, clock_in, "The clock-in time contains the original time"
        )
