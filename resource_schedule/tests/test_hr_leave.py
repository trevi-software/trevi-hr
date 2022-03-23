# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo.tests import common

from odoo.addons.mail.tests.common import mail_new_test_user


class TestHrLeave(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.HrAttendance = cls.env["hr.attendance"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrLeave = cls.env["hr.leave"]
        cls.LeaveType = cls.env["hr.leave.type"].with_context(tracking_disable=True)
        cls.ScheduleShift = cls.env["resource.schedule.shift"]

        cls.userJohn = mail_new_test_user(
            cls.env,
            login="john",
            groups="base.group_user,hr_holidays.group_hr_holidays_manager",
        )
        cls.userSally = mail_new_test_user(
            cls.env, login="sally", groups="base.group_user"
        )
        cls.eeSally = cls.HrEmployee.create(
            {"name": "Sally", "user_id": cls.userSally.id}
        )
        cls.default_calendar = cls.env.ref("resource_schedule.resource_calendar_56h")
        cls.holidays_type_1 = cls.LeaveType.create(
            {
                "name": "NotLimitedHR",
                "allocation_type": "no",
                "leave_validation_type": "hr",
                "validity_start": False,
            }
        )

    def get_start_end_dates(self, weeks=1):

        total_days = (weeks * 7) - 1
        dStart = date.today()
        while dStart.weekday() != 0:
            dStart -= timedelta(days=1)
        dEnd = dStart + timedelta(days=total_days)
        return dStart, dEnd

    def test_leave_subsumes_whole_shift(self):

        dStart, dEnd = self.get_start_end_dates()
        self.eeSally.resource_id.calendar_id = self.default_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are not shifts at all")

        shifts = self.eeSally.create_schedule(dStart, dEnd)
        count = len(shifts)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        startShift = shifts.filtered(lambda s: s.dayofweek == "0")
        self.assertEqual(len(startShift), 1, "There is one shift on Monday")

        leave_start = datetime.combine(dStart, datetime.min.time())
        leave_end = datetime.combine(dStart, datetime.strptime("23:59", "%H:%M").time())
        lv = self.HrLeave.with_user(self.userSally).create(
            {
                "name": "PTO",
                "employee_id": self.eeSally.id,
                "holiday_status_id": self.holidays_type_1.id,
                "date_from": leave_start,
                "date_to": leave_end,
                "number_of_days": 1,
            }
        )
        lv.with_user(self.userJohn).action_validate()
        self.assertEqual(lv.state, "validate", "I have validated the leave")

        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertLess(len(shifts), count, "The shift has been removed by the leave")

    def test_leave_partial_start_shift(self):

        dStart, dEnd = self.get_start_end_dates()
        self.eeSally.resource_id.calendar_id = self.default_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are not shifts at all")

        shifts = self.eeSally.create_schedule(dStart, dEnd)
        count = len(shifts)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        startShift = shifts.filtered(lambda s: s.dayofweek == "0")
        self.assertEqual(len(startShift), 1, "There is one shift on Monday")

        leave_start = datetime.combine(dStart - timedelta(days=2), datetime.min.time())
        leave_end = datetime.combine(dStart, datetime.strptime("6:30", "%H:%M").time())
        lv = self.HrLeave.with_user(self.userSally).create(
            {
                "name": "PTO",
                "employee_id": self.eeSally.id,
                "holiday_status_id": self.holidays_type_1.id,
                "date_from": leave_start,
                "date_to": leave_end,
                "number_of_days": 1,
            }
        )
        lv.with_user(self.userJohn).action_validate()
        self.assertEqual(lv.state, "validate", "I have validated the leave")

        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), count, "No shifts have been removed by the leave")
        self.assertEqual(
            shifts[0].datetime_start,
            leave_end + timedelta(seconds=1),
            "Shift start time has been altered to 1 sec. after leave ends",
        )

    def test_leave_partial_end_shift(self):

        dStart, dEnd = self.get_start_end_dates()
        self.eeSally.resource_id.calendar_id = self.default_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are not shifts at all")

        shifts = self.eeSally.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        startShift = shifts.filtered(lambda s: s.dayofweek == "0")
        self.assertEqual(len(startShift), 1, "There is one shift on Monday")

        leave_start = datetime.combine(
            dStart, datetime.strptime("13:30", "%H:%M").time()
        )
        leave_end = datetime.combine(dEnd, datetime.max.time())
        lv = self.HrLeave.with_user(self.userSally).create(
            {
                "name": "PTO",
                "employee_id": self.eeSally.id,
                "holiday_status_id": self.holidays_type_1.id,
                "date_from": leave_start,
                "date_to": leave_end,
                "number_of_days": 1,
            }
        )
        lv.with_user(self.userJohn).action_validate()
        self.assertEqual(lv.state, "validate", "I have validated the leave")

        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertEqual(
            len(shifts), 1, "All but one of the shifts has been removed by the leave"
        )
        self.assertEqual(
            shifts[0].datetime_end,
            leave_start - timedelta(seconds=1),
            "Shift end time has been altered to 1 sec. before leave starts",
        )

    def test_remove_autopunch(self):

        dStart, dEnd = self.get_start_end_dates()
        self.default_calendar.attendance_ids.autopunch = True
        self.eeSally.resource_id.calendar_id = self.default_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.eeSally.id)])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")

        # Run this test as if it was the end of the day
        now = datetime.combine(dStart, datetime.max.time())
        start = datetime.combine(dStart, datetime.min.time())
        end = now

        # Create schedule and auto-punch attendance
        #
        shifts = self.eeSally.create_schedule(dStart, dEnd)
        count = len(shifts)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        self.ScheduleShift.check_and_create_autopunch(
            self.eeSally,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.eeSally.id),
                ("check_in", ">=", start),
                ("check_out", "<=", end),
            ]
        )
        monday_att_ids = punches.filtered(lambda p: p.check_in.weekday() == 0).ids
        self.assertEqual(
            len(monday_att_ids), 1, "I was able to create hr.attendance records."
        )

        # Create Leave
        #
        leave_start = datetime.combine(dStart, datetime.min.time())
        leave_end = datetime.combine(dStart, datetime.strptime("23:59", "%H:%M").time())
        lv = self.HrLeave.with_user(self.userSally).create(
            {
                "name": "PTO",
                "employee_id": self.eeSally.id,
                "holiday_status_id": self.holidays_type_1.id,
                "date_from": leave_start,
                "date_to": leave_end,
                "number_of_days": 1,
            }
        )
        lv.with_user(self.userJohn).action_validate()
        self.assertEqual(lv.state, "validate", "I have validated the leave")

        # Test
        #
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertLess(len(shifts), count, "The shift has been removed by the leave")
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.eeSally.id),
                ("id", "in", monday_att_ids),
            ]
        )
        self.assertFalse(punches, "The attendance record for Monday has been removed")

    def test_modify_autopunch(self):

        dStart, dEnd = self.get_start_end_dates()
        self.default_calendar.attendance_ids.autopunch = True
        self.eeSally.resource_id.calendar_id = self.default_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.eeSally.id)])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")

        # Run this test as if it was the end of the day
        now = datetime.combine(dStart, datetime.max.time())
        start = datetime.combine(dStart, datetime.min.time())
        end = now

        # Create schedule and auto-punch attendance
        #
        initShifts = self.eeSally.create_schedule(dStart, dEnd)
        self.assertGreater(len(initShifts), 0, "I was able to create shifts")

        self.ScheduleShift.check_and_create_autopunch(
            self.eeSally,
            initShifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.eeSally.id),
                ("check_in", ">=", start),
                ("check_out", "<=", end),
            ]
        )
        monday_att_ids = punches.filtered(lambda p: p.check_in.weekday() == 0).ids
        self.assertEqual(
            len(monday_att_ids), 1, "I was able to create hr.attendance records."
        )

        # Create Leave - last day of leave overlaps start time of shift
        #
        leave_start = datetime.combine(
            dStart - relativedelta(days=4), datetime.min.time()
        )
        leave_end = datetime.combine(
            dStart, datetime.strptime("7:29:59", "%H:%M:%S").time()
        )
        lv = self.HrLeave.with_user(self.userSally).create(
            {
                "name": "PTO",
                "employee_id": self.eeSally.id,
                "holiday_status_id": self.holidays_type_1.id,
                "date_from": leave_start,
                "date_to": leave_end,
                "number_of_days": 1,
            }
        )
        lv.with_user(self.userJohn).action_validate()
        self.assertEqual(lv.state, "validate", "I have validated the leave")

        # Test
        #
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertEqual(
            shifts, initShifts, "The shifts are the same after leave creation"
        )
        monAtt = punches.filtered(lambda a: a.check_in.weekday() == 0)
        self.assertTrue(monAtt, "I found an attendance for Monday")
        self.assertEqual(
            monAtt.check_in,
            datetime.combine(dStart, datetime.strptime("7:30", "%H:%M").time()),
            "The attendance has been modified according to the leave",
        )

    def test_modify_autopunch2(self):

        dStart, dEnd = self.get_start_end_dates()
        self.default_calendar.attendance_ids.autopunch = True
        self.eeSally.resource_id.calendar_id = self.default_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.eeSally.id)])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")

        # Run this test as if it was the end of the day
        now = datetime.combine(dStart, datetime.max.time())
        start = datetime.combine(dStart, datetime.min.time())
        end = now

        # Create schedule and auto-punch attendance
        #
        initShifts = self.eeSally.create_schedule(dStart, dEnd)
        self.assertGreater(len(initShifts), 0, "I was able to create shifts")

        self.ScheduleShift.check_and_create_autopunch(
            self.eeSally,
            initShifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.eeSally.id),
                ("check_in", ">=", start),
                ("check_out", "<=", end),
            ]
        )
        monday_att_ids = punches.filtered(lambda p: p.check_in.weekday() == 0).ids
        self.assertEqual(
            len(monday_att_ids), 1, "I was able to create hr.attendance records."
        )

        # Create Leave - first day of leave overlaps end time of shift
        #
        leave_start = datetime.combine(
            dStart, datetime.strptime("12:30:00", "%H:%M:%S").time()
        )
        leave_end = datetime.combine(
            dStart + relativedelta(days=1), datetime.max.time()
        )
        lv = self.HrLeave.with_user(self.userSally).create(
            {
                "name": "PTO",
                "employee_id": self.eeSally.id,
                "holiday_status_id": self.holidays_type_1.id,
                "date_from": leave_start,
                "date_to": leave_end,
                "number_of_days": 1,
            }
        )
        lv.with_user(self.userJohn).action_validate()
        self.assertEqual(lv.state, "validate", "I have validated the leave")

        # Test
        #
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeSally.resource_id.id),
            ]
        )
        self.assertNotEqual(
            shifts, initShifts, "The shifts are *NOT* the same after leave creation"
        )
        monAtt = punches.filtered(lambda a: a.check_in.weekday() == 0)
        self.assertTrue(monAtt, "I found an attendance for Monday")
        self.assertEqual(
            monAtt.check_out,
            datetime.combine(dStart, datetime.strptime("12:29:59", "%H:%M:%S").time()),
            "The attendance has been modified according to the leave",
        )
