# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime, timedelta

from pytz import timezone, utc

from odoo.exceptions import ValidationError
from odoo.tests import Form, common

from odoo.addons.resource.models.resource import float_to_time


class TestResourceScheduleShift(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.HrAttendance = cls.env["hr.attendance"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.ScheduleShift = cls.env["resource.schedule.shift"]
        cls.AttendanceTemplate = cls.env["resource.calendar.attendance.template"]

        cls.employee = cls.HrEmployee.create({"name": "John"})
        cls.eeSally = cls.HrEmployee.create({"name": "Sally"})
        cls.sunday = cls.env.ref("resource_schedule.wd_sun")
        cls.tuesday = cls.env.ref("resource_schedule.wd_tue")
        cls.att_template = cls.env.ref("resource_schedule.attendance_template_demo0")
        cls.flex_workday_template = cls.env.ref(
            "resource_schedule.attendance_template_demo11"
        )
        cls.area_1 = cls.env.ref("resource_schedule.schedule_area0")
        cls.area_2 = cls.env.ref("resource_schedule.schedule_area1")
        cls.default_calendar = cls.env.ref("resource_schedule.resource_calendar_44h")
        cls.std35_calendar = cls.env.ref("resource.resource_calendar_std_35h")
        cls.production_calendar = cls.env.ref("resource_schedule.resource_calendar_56h")
        cls.empty_calendar = cls.env["resource.calendar"].create(
            {
                "name": "Standard 0 hours/week",
            }
        )
        cls.empty_calendar.attendance_ids.unlink()
        cls.night_template = cls.AttendanceTemplate.create(
            {
                "name": "graveyard shift",
                "hour_from": 22,
                "hour_to": 6,
                "day_period": "evening",
                "span_midnight": True,
                "autopunch": True,
            }
        )
        cls.night_calendar = cls.env["resource.calendar"].create(
            {
                "name": "Night Calendar",
                "attendance_ids": [
                    (0, 0, {"template_id": cls.night_template.id, "dayofweek": "0"}),
                    (0, 0, {"template_id": cls.night_template.id, "dayofweek": "1"}),
                    (0, 0, {"template_id": cls.night_template.id, "dayofweek": "2"}),
                    (0, 0, {"template_id": cls.night_template.id, "dayofweek": "3"}),
                    (0, 0, {"template_id": cls.night_template.id, "dayofweek": "4"}),
                    (0, 0, {"template_id": cls.night_template.id, "dayofweek": "5"}),
                    (0, 0, {"template_id": cls.night_template.id, "dayofweek": "6"}),
                ],
            }
        )

    def create_contract(
        self,
        employee_id=None,
        state="draft",
        kanban_state="normal",
        start=None,
        end=None,
        trial_end=None,
        wage=1,
        calendar_id=None,
    ):

        if employee_id is None:
            employee_id = self.employee.id
        if start is None:
            start = date.today()

        res = {
            "name": "Contract",
            "employee_id": employee_id,
            "state": state,
            "kanban_state": kanban_state,
            "wage": wage,
            "date_start": start,
            "trial_date_end": trial_end,
            "date_end": end,
        }
        if calendar_id is not None:
            res.update({"resource_calendar_id": calendar_id})

        return self.env["hr.contract"].create(res)

    def apply_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def get_start_end_dates(self, weeks=1):

        total_days = (weeks * 7) - 1
        dStart = date.today()
        while dStart.weekday() != 0:
            dStart -= timedelta(days=1)
        dEnd = dStart + timedelta(days=total_days)
        return dStart, dEnd

    def localize_dt(self, dt, tz, reverse=False):
        """
        Localize naive dt from database (UTC) to timzezone tz. If reverse is True
        a naive dt that is in timezone tz is converted to naive dt for storage in db.
        """

        local_tz = timezone(tz)
        if not reverse:
            res = utc.localize(dt, is_dst=False).astimezone(local_tz)
        else:
            res = (
                local_tz.localize(dt, is_dst=False).astimezone(utc).replace(tzinfo=None)
            )
        return res

    def test_record_order(self):

        c = self.create_contract(calendar_id=self.default_calendar.id)
        self.apply_cron()

        prevShift = None
        for shift in c.employee_id.resource_id.scheduled_shift_ids:
            if prevShift is None:
                prevShift = shift.datetime_start
                continue

            self.assertGreater(
                shift.datetime_start,
                prevShift,
                "Shifts are ordered in order of start datetime",
            )

    def test_compute_employee(self):

        self.assertGreater(
            len(self.default_calendar.attendance_ids),
            0,
            "The default calendar has work details",
        )

        shifts = self.ScheduleShift.create_schedule(
            self.employee.resource_id,
            date.today(),
            date.today() + timedelta(days=6),
            self.default_calendar,
        )
        for shift in shifts:
            self.assertEqual(
                shift.employee_id,
                self.employee,
                "The work details of the calendar point to the employee",
            )

    def test_duration(self):

        shifts = self.ScheduleShift.create_schedule(
            self.employee.resource_id,
            date.today(),
            date.today() + timedelta(days=6),
            self.default_calendar,
        )
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        for shift in shifts:
            if shift.dayofweek != "5":
                self.assertEqual(
                    shift.duration,
                    28800,
                    "Duration of 9 hour workday with break is 28800 seconds",
                )
            else:
                self.assertEqual(
                    shift.duration,
                    16200,
                    "Duration of 1/2 workday without break is 16200 seconds",
                )
            attendance_ids = self.default_calendar.attendance_ids.filtered(
                lambda s: s.dayofweek == shift.dayofweek
                and s.hour_from == shift.hour_from
            )
            self.assertEqual(
                shift.duration,
                attendance_ids.duration,
                "Duration of shift equals duration of the corresponding work detail",
            )

    def test_end_middle_of_week(self):

        start = date.today()
        # end the shift on a wednesday
        end = start + timedelta(days=7)
        while end.weekday() != 2:
            end += timedelta(days=1)

        shifts = self.ScheduleShift.create_schedule(
            self.employee.resource_id, start, end, self.default_calendar
        )
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        self.assertEqual(shifts[-1].dayofweek, "2", "The last shift is on a wednesday")

    # Because sunday is a boundary of Work Schedules (resource.calendar)
    def test_date_range_end_sunday(self):

        start = date.today()
        # The end date is on a sunday
        end = start + timedelta(days=7)
        while end.weekday() != 6:
            end += timedelta(days=1)

        shifts = self.ScheduleShift.create_schedule(
            self.employee.resource_id, start, end, self.default_calendar
        )
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        self.assertEqual(
            shifts[-1].dayofweek,
            "5",
            "The last shift is on a saturday (becuase sunday is not scheduled)",
        )

    # Because of a bug I found when working with a 5-day work week
    def test_date_range_end_sunday_2(self):

        start = date.today()
        # The end date is on a sunday
        end = start + timedelta(days=7)
        while end.weekday() != 6:
            end += timedelta(days=1)

        self.assertEqual(
            self.std35_calendar.attendance_ids[-1].dayofweek,
            "4",
            "Last day of the work details is Friday",
        )

        shifts = self.ScheduleShift.create_schedule(
            self.employee.resource_id, start, end, self.std35_calendar
        )
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        self.assertEqual(
            shifts[-1].dayofweek,
            "4",
            "The last shift is on a friday (becuase sat & sun aren't scheduled)",
        )

    def test_onchange_resource(self):

        self.employee.resource_id.calendar_id = self.std35_calendar
        self.eeSally.resource_id.calendar_id = self.default_calendar

        frmShift = Form(self.ScheduleShift)
        self.assertFalse(
            frmShift.calendar_id, "Initially the Work Times field is blank"
        )

        frmShift.resource_id = self.employee.resource_id
        self.assertEqual(
            frmShift.calendar_id,
            self.std35_calendar,
            "The Work Times field contains resource's default Work Time",
        )

        frmShift.resource_id = self.eeSally.resource_id
        self.assertEqual(
            frmShift.calendar_id,
            self.default_calendar,
            "The Work Times field contains new resource's default Work Time",
        )

    def test_onchange_resource_2(self):

        self.att_template.default_area_id = self.area_1
        self.employee.resource_id.calendar_id = self.production_calendar

        frmShift = Form(self.ScheduleShift)
        frmShift.resource_id = self.employee.resource_id
        self.assertEqual(
            frmShift.default_area_id,
            self.area_1,
            "The default area contains the area defined on the template",
        )

        self.employee.resource_id.default_area_id = self.area_2
        frmShift = Form(self.ScheduleShift)
        frmShift.resource_id = self.employee.resource_id
        self.assertEqual(
            frmShift.default_area_id,
            self.area_2,
            "The default area contains the area defined on the resource",
        )

    def test_onchange_calendar(self):

        self.employee.resource_id.calendar_id = self.production_calendar
        frmShift = Form(self.ScheduleShift)
        self.assertEqual(
            frmShift.dayofweek, "0", "The default dayofweek fields is Monday"
        )

        frmShift.resource_id = self.employee.resource_id
        self.assertEqual(
            frmShift.calendar_id,
            self.production_calendar,
            "The Work Times field contains resource's default Work Time",
        )
        self.assertEqual(
            frmShift.day_period,
            "8day",
            "The day period is consistent with the initial Work Time",
        )
        self.assertEqual(
            frmShift.hour_to,
            17,
            "The end time is consistent with the initial Work Time",
        )

        if not frmShift.datetime_start:
            frmShift.datetime_start = date.today()

        # Change to empty calendar
        frmShift.calendar_id = self.empty_calendar
        self.assertFalse(
            frmShift.day_period,
            "The day period is the default value",
        )

        # Change to 5 day calendar, 7 hrs/day
        frmShift.calendar_id = self.std35_calendar

        # Today is monday - friday
        if date.today().weekday() not in [5, 6]:
            self.assertEqual(
                frmShift.day_period,
                "morning",
                "The day period is consistent with the new Work Time",
            )
            self.assertEqual(
                frmShift.hour_to,
                12,
                "The end time is consistent with the new Work Time",
            )
        # Today is sat - sun
        else:
            self.assertFalse(
                frmShift.day_period,
                "The day period is the default value",
            )
            self.assertFalse(frmShift.hour_to, "The end time is the default value")
        self.assertEqual(
            frmShift.dayofweek,
            str(date.today().weekday()),
            "The dayofweek fields is consistent with the start date",
        )

    def test_create_schedule_default_offday(self):

        dStart, dEnd = self.get_start_end_dates()
        self.employee.resource_id.calendar_id = self.production_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are not shifts at all")

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        day_list = shifts.mapped("dayofweek")
        self.assertEqual(
            day_list,
            ["0", "1", "2", "3", "4", "5"],
            "The default day off was not scheduled",
        )

    def test_create_schedule_employee_offday(self):

        dStart, dEnd = self.get_start_end_dates()
        self.production_calendar.dayoff_type = "fix_one"
        self.employee.resource_id.calendar_id = self.production_calendar
        self.employee.resource_id.write({"dayoff_ids": [(6, 0, [self.tuesday.id])]})

        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        day_list = shifts.mapped("dayofweek")
        self.assertEqual(
            day_list,
            ["0", "2", "3", "4", "5", "6"],
            "The default day off was not scheduled",
        )

    def test_create_schedule_rolling_offday(self):

        dStart, dEnd = self.get_start_end_dates(weeks=3)
        self.production_calendar.dayoff_type = "rolling"
        self.employee.resource_id.calendar_id = self.production_calendar
        self.employee.resource_id.write({"dayoff_ids": [(6, 0, [self.tuesday.id])]})

        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        day_list = [shift.dayofweek for shift in shifts]
        self.assertEqual(
            day_list,
            [
                "0",
                "2",
                "3",
                "4",
                "5",
                "6",
                "1",
                "2",
                "3",
                "4",
                "5",
                "0",
                "1",
                "2",
                "3",
                "4",
                "6",
            ],
            "The rolling days off in the 3 week period are: tue, mon, sun, sat",
        )

    def test_night_shift(self):

        dStart, dEnd = self.get_start_end_dates()
        self.employee.resource_id.calendar_id = (self.night_calendar,)
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are not shifts at all")

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        today = dStart
        for shift in shifts:
            dtShiftStart = datetime.combine(
                today, float_to_time(self.night_template.hour_from)
            )
            tzLocal = timezone(self.night_calendar.tz)
            dtShiftStart = (
                tzLocal.localize(dtShiftStart, is_dst=False)
                .astimezone(utc)
                .replace(tzinfo=None)
            )
            dtShiftEnd = datetime.combine(
                today + timedelta(days=1), float_to_time(self.night_template.hour_to)
            )
            dtShiftEnd = (
                tzLocal.localize(dtShiftEnd, is_dst=False)
                .astimezone(utc)
                .replace(tzinfo=None)
            )
            self.assertTrue(
                shift.span_midnight, "The shift has the field 'span_midnight' set"
            )
            self.assertEqual(
                shift.datetime_start, dtShiftStart, "Shift start time is today"
            )
            self.assertEqual(
                shift.datetime_end, dtShiftEnd, "Shift end time is tomorrow"
            )

            today += timedelta(days=1)

    def test_flex_night_shift(self):

        self.flex_workday_template.span_midnight = True
        self.flex_workday_template.hour_from = 18
        self.flex_workday_template.hour_to = 6
        self.flex_workday_template.flex_core_from = 22
        self.flex_workday_template.flex_core_to = 4
        dStart, dEnd = self.get_start_end_dates()
        self.empty_calendar.attendance_ids.unlink()
        self.empty_calendar.attendance_ids = [
            (0, 0, {"dayofweek": "0", "template_id": self.flex_workday_template.id}),
            (0, 0, {"dayofweek": "1", "template_id": self.flex_workday_template.id}),
            (0, 0, {"dayofweek": "2", "template_id": self.flex_workday_template.id}),
            (0, 0, {"dayofweek": "3", "template_id": self.flex_workday_template.id}),
            (0, 0, {"dayofweek": "4", "template_id": self.flex_workday_template.id}),
            (0, 0, {"dayofweek": "5", "template_id": self.flex_workday_template.id}),
            (0, 0, {"dayofweek": "6", "template_id": self.flex_workday_template.id}),
        ]
        self.employee.resource_id.calendar_id = self.empty_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are not shifts at all")

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        today = dStart
        for shift in shifts:
            dtShiftStart = datetime.combine(today, float_to_time(18))
            dtShiftEnd = datetime.combine(today + timedelta(days=1), float_to_time(6))
            tzLocal = timezone(self.empty_calendar.tz)
            dtShiftStart = (
                tzLocal.localize(dtShiftStart, is_dst=False)
                .astimezone(utc)
                .replace(tzinfo=None)
            )
            dtShiftEnd = (
                tzLocal.localize(dtShiftEnd, is_dst=False)
                .astimezone(utc)
                .replace(tzinfo=None)
            )
            self.assertEqual(shift.shift_type, "flex", "The shift is a flex shift")
            self.assertEqual(
                shift.flex_scheduled_hrs, 8, "The flex scheduled hours are 8"
            )
            self.assertEqual(
                shift.flex_core_from, 22, "The shift has the correct core from time"
            )
            self.assertEqual(
                shift.flex_core_to, 4, "The shift has the correct core to time"
            )
            self.assertTrue(
                shift.span_midnight, "The shift has the field 'span_midnight' set"
            )
            self.assertEqual(
                shift.datetime_start, dtShiftStart, "Shift start time is today"
            )
            self.assertEqual(
                shift.datetime_end, dtShiftEnd, "Shift end time is tomorrow"
            )

            today += timedelta(days=1)

    def test_no_autopunch(self):

        dStart, dEnd = self.get_start_end_dates()
        self.employee.resource_id.calendar_id = self.production_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.employee.id)])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")

        # Run this test as if it was the end of the day
        now = datetime.combine(dStart, datetime.max.time())

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")
        self.assertFalse(shifts[0].autopunch, "The shifts *do not* have autopunch set")

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(
            len(punches),
            0,
            "If autopunch is *not* set attendance records are not created.",
        )

    def test_autopunch(self):

        dStart, dEnd = self.get_start_end_dates()
        self.employee.resource_id.calendar_id = self.production_calendar
        self.production_calendar.attendance_ids.autopunch = True
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.employee.id)])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")

        # Run this test as if it was the end of the day
        tzLocal = timezone(self.production_calendar.tz)
        now = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.max.time()), is_dst=False
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        start = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.min.time()), is_dst=False
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        end = now

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")
        self.assertTrue(shifts[0].autopunch, "The shifts have autopunch set")

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
                ("check_in", ">=", start),
                ("check_out", "<=", end),
            ]
        )
        self.assertEqual(len(punches), 1, "I was able to create hr.attendance records.")

        dtShiftStart = (
            tzLocal.localize(datetime.combine(dStart, float_to_time(8)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        dtShiftEnd = (
            tzLocal.localize(datetime.combine(dStart, float_to_time(17)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        self.assertEqual(
            punches[0].check_in,
            dtShiftStart,
            "Start date and time of hr.attendance record is correct",
        )
        self.assertEqual(
            punches[0].check_out,
            dtShiftEnd,
            "End date and time of hr.attendance record is correct",
        )

    def test_autopunch_span_midnight(self):

        dStart, dEnd = self.get_start_end_dates()
        self.employee.resource_id.calendar_id = self.night_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.employee.id)])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")

        # Run this test as if it was the end of the day
        now = datetime.combine(dStart, datetime.max.time())

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")
        self.assertTrue(shifts[0].autopunch, "The shifts have autopunch set")

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(len(punches), 1, "I was able to create hr.attendance records.")

        tzLocal = timezone(self.night_calendar.tz)
        dtShiftStart = (
            tzLocal.localize(datetime.combine(dStart, float_to_time(22)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        dtShiftEnd = (
            tzLocal.localize(
                datetime.combine(dStart + timedelta(days=1), float_to_time(6)),
                is_dst=False,
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        self.assertEqual(
            punches[0].check_in,
            dtShiftStart,
            "Start date and time of hr.attendance record is correct",
        )
        self.assertFalse(
            punches[0].check_out,
            "The employee hasn't been punched out because the shift hasn't ended yet",
        )

        # Move time forward 7 hours (next day 7 am)
        now += timedelta(hours=7)
        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )

        self.assertEqual(
            punches[0].check_out,
            dtShiftEnd,
            "End date and time of hr.attendance record is correct",
        )

    def test_autopunch_multiple_shifts(self):

        tpl_morn = self.AttendanceTemplate.create(
            {
                "name": "Morning",
                "hour_from": 8,
                "hour_to": 12,
                "day_period": "morning",
                # "autopunch": True,
            }
        )
        tpl_noon = self.AttendanceTemplate.create(
            {
                "name": "Afternoon",
                "hour_from": 13,
                "hour_to": 16,
                "day_period": "afternoon",
                # "autopunch": True,
            }
        )
        self.std35_calendar.attendance_ids = [
            (0, 0, {"template_id": tpl_morn.id, "dayofweek": "5"}),
            (0, 0, {"template_id": tpl_noon.id, "dayofweek": "5"}),
            (0, 0, {"template_id": tpl_morn.id, "dayofweek": "6"}),
            (0, 0, {"template_id": tpl_noon.id, "dayofweek": "6"}),
        ]
        self.std35_calendar.attendance_ids.autopunch = True
        dStart, dEnd = self.get_start_end_dates()
        self.employee.resource_id.calendar_id = self.std35_calendar
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.employee.id)])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")
        self.assertTrue(shifts[0].autopunch, "The shifts have autopunch set")

        tzLocal = timezone(self.std35_calendar.tz)
        now = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.strptime("7:59", "%H:%M").time()),
                is_dst=False,
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(
            len(punches), 0, "No punches created before scheduled shift start"
        )

        now = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.strptime("11:59", "%H:%M").time()),
                is_dst=False,
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(len(punches), 1, "One attendance created before lunch starts")

        tzLocal = timezone(self.night_calendar.tz)
        dtShiftStart = (
            tzLocal.localize(datetime.combine(dStart, float_to_time(8)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        dtShiftEnd = (
            tzLocal.localize(datetime.combine(dStart, float_to_time(12)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        self.assertEqual(
            punches[0].check_in,
            dtShiftStart,
            "Start date/time of hr.attendance record is correct",
        )
        self.assertFalse(
            punches[0].check_out,
            "The out-punch is empty because check-out time hasn't arrived yet",
        )

        now = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.strptime("12:00", "%H:%M").time()),
                is_dst=False,
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(len(punches), 1, "Still only one attendance created")
        self.assertEqual(
            punches[0].check_in,
            dtShiftStart,
            "Start date/time of hr.attendance record is correct",
        )
        self.assertEqual(
            punches[0].check_out,
            dtShiftEnd,
            "End date/time of hr.attendance record is correct",
        )
        saved_punches = punches
        saved_checkin = punches[0].check_in
        saved_checkout = punches[0].check_out

        now = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.strptime("12:30", "%H:%M").time()),
                is_dst=False,
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(
            punches, saved_punches, "No changes between first shift and second"
        )
        self.assertEqual(
            punches[0].check_in, saved_checkin, "Check-in time hasn't changed"
        )
        self.assertEqual(
            punches[0].check_out, saved_checkout, "Check-out time hasn't changed"
        )

        now = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.strptime("13:00", "%H:%M").time()),
                is_dst=False,
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(len(punches), 2, "Two attendance records created")

        tzLocal = timezone(self.std35_calendar.tz)
        dtShiftStart = (
            tzLocal.localize(datetime.combine(dStart, float_to_time(13)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        dtShiftEnd = (
            tzLocal.localize(datetime.combine(dStart, float_to_time(16)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        self.assertEqual(
            punches[0].check_in,
            dtShiftStart,
            "Start date/time of hr.attendance record is correct",
        )
        self.assertFalse(
            punches[0].check_out, "End date/time of hr.attendance record is False"
        )

        now = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.strptime("16:30", "%H:%M").time()),
                is_dst=False,
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )

        self.ScheduleShift.check_and_create_autopunch(
            self.employee,
            shifts.filtered(lambda s: s.day == dStart),
            now,
        )
        punches = self.HrAttendance.search(
            [
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(len(punches), 2, "Two attendance records created")
        self.assertEqual(
            punches[0].check_in,
            dtShiftStart,
            "Start date/time of hr.attendance record is correct",
        )
        self.assertEqual(
            punches[0].check_out,
            dtShiftEnd,
            "End date/time of hr.attendance record is correct",
        )
        self.assertEqual(
            punches[1].check_in,
            saved_checkin,
            "Check-in time of first shift hasn't changed",
        )
        self.assertEqual(
            punches[1].check_out,
            saved_checkout,
            "Check-out time of first shift hasn't changed",
        )

    def test_conflicting_autopunch(self):

        dStart, dEnd = self.get_start_end_dates()
        self.employee.resource_id.calendar_id = self.production_calendar
        self.production_calendar.attendance_ids.autopunch = True
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.employee.id)])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")
        self.assertTrue(shifts[0].autopunch, "The shifts have autopunch set")

        # Create a punch that conflicts with the schedule
        self.HrAttendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime.combine(
                    dStart, datetime.strptime("3:00", "%H:%M").time()
                ),
                "check_out": datetime.combine(
                    dStart, datetime.strptime("12:00", "%H:%M").time()
                ),
            }
        )
        now = datetime.combine(dStart, datetime.strptime("12:00", "%H:%M").time())

        with self.assertRaises(ValidationError):
            self.ScheduleShift.check_and_create_autopunch(
                self.employee,
                shifts.filtered(lambda s: s.day == dStart),
                now,
            )

    def test_autopunch_missed_run(self):

        LastRun = self.env["resource.schedule.autopunch.lastrun"]
        dStart, dEnd = self.get_start_end_dates()
        self.employee.resource_id.calendar_id = self.production_calendar
        self.production_calendar.attendance_ids.autopunch = True
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.employee.resource_id.id),
            ]
        )
        punches = self.HrAttendance.search([("employee_id", "=", self.employee.id)])
        lastrun = LastRun.search([])
        self.assertEqual(len(shifts), 0, "Initialy, there are no shifts at all")
        self.assertEqual(len(punches), 0, "Initialy, there are no attendances at all")
        self.assertEqual(len(lastrun), 0, "Initialyy, there are no last-run records")

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")
        self.assertTrue(shifts[0].autopunch, "The shifts have autopunch set")

        tzLocal = timezone(self.production_calendar.tz)
        now = (
            tzLocal.localize(
                datetime.combine(dStart, datetime.strptime("15:45", "%H:%M").time()),
                is_dst=False,
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        punches = self.ScheduleShift._autopunch_shifts(now)
        lastrun = LastRun.search([])
        self.assertEqual(len(punches), 1, "There is one attendance record")
        self.assertFalse(punches[0].check_out, "Check-out time hasn't arrived yet")
        self.assertEqual(
            lastrun[0].name,
            now,
            "Last run record matches the last time autopunch was run",
        )
        self.assertEqual(
            lastrun[0].record_count, 1, "Only the one punch from the detail was created"
        )

        # wednesday
        now += timedelta(days=2)
        dWed = now.date()
        dTue = dWed - timedelta(days=1)
        punches = self.ScheduleShift._autopunch_shifts(now)
        lastrun = LastRun.search([])
        self.assertEqual(
            len(punches), 3, "There are 3 attendance records (mon, tue, wed)"
        )
        lastrun = LastRun.search([])

        dtShiftEnd = (
            tzLocal.localize(datetime.combine(dStart, float_to_time(17)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        self.assertEqual(
            punches[2].check_out,
            dtShiftEnd,
            "End date/time of monday is now filled in",
        )

        dtShiftStart = (
            tzLocal.localize(datetime.combine(dTue, float_to_time(8)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        self.assertEqual(
            punches[1].check_in,
            dtShiftStart,
            "Start date/time of tuesday is now filled in",
        )

        dtShiftEnd = (
            tzLocal.localize(datetime.combine(dTue, float_to_time(17)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        self.assertEqual(
            punches[1].check_out,
            dtShiftEnd,
            "End date/time of tuesday is now filled in",
        )

        dtShiftStart = (
            tzLocal.localize(datetime.combine(dWed, float_to_time(8)), is_dst=False)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        self.assertEqual(
            punches[0].check_in,
            dtShiftStart,
            "Start date/time of wednesday is now filled in",
        )
        self.assertFalse(
            punches[0].check_out, "Wednesday's check-out time hasn't arrived yet"
        )

    def test_datetimes(self):

        # when writing directly to DB it is assumed the datetime is already in UTC
        dtStart = datetime.combine(
            date.today(), datetime.strptime("0530", "%H%M").time()
        )
        dtEnd = datetime.combine(date.today(), datetime.strptime("1330", "%H%M").time())
        self.employee.resource_id.tz = "Africa/Addis_Ababa"
        shift = self.ScheduleShift.create(
            {
                "resource_id": self.employee.resource_id.id,
                "calendar_id": self.default_calendar.id,
                "datetime_start": dtStart,
                "datetime_end": dtEnd,
            }
        )

        self.assertEqual(
            shift.tz,
            "Africa/Addis_Ababa",
            "The shift has the correct timezone",
        )
        self.assertEqual(
            shift.datetimes_naive_utc(),
            [(dtStart, dtEnd, shift)],
            "The start and end shift times are identical to those supplied",
        )
        self.assertEqual(
            shift.datetimes_naive_tz(),
            [(dtStart + timedelta(hours=3), dtEnd + timedelta(hours=3), shift)],
            "The start and end shift times have been converted to the timezone",
        )
