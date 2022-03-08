# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.tests import common


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
        cls.area_1 = cls.env.ref("resource_schedule.schedule_area0")
        cls.area_2 = cls.env.ref("resource_schedule.schedule_area1")
        cls.default_calendar = cls.env.ref("resource_schedule.resource_calendar_44h")
        cls.std35_calendar = cls.env.ref("resource.resource_calendar_std_35h")
        cls.production_calendar = cls.env.ref("resource_schedule.resource_calendar_56h")
        cls.dupont_calendar = cls.env.ref("resource_schedule.resource_calendar_dupont")

    def get_start_end_dates(self, weeks=1):

        total_days = (weeks * 7) - 1
        dStart = date.today()
        while dStart.weekday() != 0:
            dStart -= timedelta(days=1)
        dEnd = dStart + timedelta(days=total_days)
        return dStart, dEnd

    def test_schedule_team(self):

        dStart, dEnd = self.get_start_end_dates(weeks=1)
        employees = self.employee | self.eeSally
        teamA = self.env.ref("resource_schedule.schedule_team0")
        teamB = self.env.ref("resource_schedule.schedule_team1")
        teamA.resource_calendar_id = self.dupont_calendar
        teamA.start_week = 0
        teamB.resource_calendar_id = self.dupont_calendar
        teamB.start_week = 1
        self.employee.resource_id.schedule_team_id = teamA
        self.eeSally.resource_id.schedule_team_id = teamB
        shifts = self.ScheduleShift.search(
            [
                (
                    "resource_id",
                    "in",
                    [self.employee.resource_id.id, self.eeSally.resource_id.id],
                ),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are not shifts at all")
        self.assertIn(
            self.employee.resource_id,
            teamA.resource_ids,
            "The employee is in the proper team",
        )
        self.assertIn(
            self.eeSally.resource_id,
            teamB.resource_ids,
            "The employee (Sally) is in the proper team",
        )

        shifts = employees.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        employeeShifts = shifts.filtered(
            lambda s: s.resource_id == self.employee.resource_id
        )
        day_list = employeeShifts.mapped("dayofweek")
        sequence_list = employeeShifts.mapped("sequence")
        self.assertEqual(
            employeeShifts[0].calendar_id,
            self.dupont_calendar,
            "The employee's shift schedule is based on the Dupont calendar",
        )
        self.assertEqual(
            sequence_list,
            [11, 12, 13, 14],
            "The sequence of the shifts matches the sequence in the 1st week",
        )
        self.assertEqual(
            day_list,
            ["0", "1", "2", "3"],
            "The employee in Team A started in week 0",
        )

        sallyShifts = shifts.filtered(
            lambda s: s.resource_id == self.eeSally.resource_id
        )
        day_list = sallyShifts.mapped("dayofweek")
        sequence_list = sallyShifts.mapped("sequence")
        self.assertEqual(
            sallyShifts[0].calendar_id,
            self.dupont_calendar,
            "Sally's shift schedule is based on the Dupont calendar",
        )
        self.assertEqual(
            sequence_list,
            [21, 22, 23, 24, 25, 26],
            "The sequence of the shifts matches the sequence in the 2nd week",
        )
        self.assertEqual(
            day_list,
            ["0", "1", "2", "4", "5", "6"],
            "The employee in Team B started in week 1",
        )

    def test_schedule_dupont(self):

        dStart, dEnd = self.get_start_end_dates(weeks=4)
        teamA = self.env.ref("resource_schedule.schedule_team0")
        teamA.resource_calendar_id = self.dupont_calendar
        teamA.start_week = 1
        self.employee.resource_id.schedule_team_id = teamA
        shifts = self.ScheduleShift.search(
            [
                ("resource_id", "in", [self.employee.resource_id.id]),
            ]
        )
        self.assertEqual(len(shifts), 0, "Initialy, there are not shifts at all")
        self.assertIn(
            self.employee.resource_id,
            teamA.resource_ids,
            "The employee is in the proper team",
        )

        shifts = self.employee.create_schedule(dStart, dEnd)
        self.assertGreater(len(shifts), 0, "I was able to create shifts")

        employeeShifts = shifts.filtered(
            lambda s: s.resource_id == self.employee.resource_id
        )
        day_list = []
        for shift in employeeShifts:
            day_list += shift.dayofweek
        sequence_list = employeeShifts.mapped("sequence")

        self.assertEqual(
            employeeShifts[0].calendar_id,
            self.dupont_calendar,
            "The employee's shift schedule is based on the team's calendar",
        )
        self.assertEqual(
            sequence_list,
            [21, 22, 23, 24, 25, 26, 31, 32, 33, 34, 11, 12, 13, 14],
            "The sequence of the shifts matches the sequence in the dupont calendar",
        )
        self.assertEqual(
            day_list,
            ["0", "1", "2", "4", "5", "6", "3", "4", "5", "6", "0", "1", "2", "3"],
            "The schedule wrapped arround from the start week to the previous one",
        )
        self.assertEqual(
            (shifts[10].datetime_start - shifts[9].datetime_end).days - 1,
            7,
            "There is a gap of 7 days in schedule for the last week of dupont cycle",
        )
