# Copyright (C) 2022,2023 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestResourceScheduleCommon(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.HrAttendance = cls.env["hr.attendance"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.ScheduleShift = cls.env["resource.schedule.shift"]
        cls.AttendanceTemplate = cls.env["resource.calendar.attendance.template"]
        cls.ScheduleGroup = cls.env["resource.schedule.group"]
        cls.ScheduleArea = cls.env["resource.schedule.area"]
        cls.ScheduleTeam = cls.env["resource.schedule.team"]
        cls.Calendar = cls.env["resource.calendar"]

        # Areas
        cls.area_1 = cls.ScheduleArea.create({"name": "Main Dining", "color": 1})
        cls.area_2 = cls.ScheduleArea.create({"name": "Bar", "color": 3})
        cls.area_3 = cls.ScheduleArea.create({"name": "Lobby", "color": 5})

        # Schedule Groups
        cls.schedule_group_0 = cls.ScheduleGroup.create({"name": "Kitchen"})
        cls.schedule_group_3 = cls.ScheduleGroup.create({"name": "Office"})

        # Attendance Templates
        cls.att_template = cls.AttendanceTemplate.create(
            {
                "name": "Weekday hours",
                "hour_from": 8,
                "hour_to": 17,
                "day_period": "8day",
                "autodeduct_break": True,
                "break_minutes": 60,
                "schedule_group_ids": [(6, 0, [cls.schedule_group_3.id])],
            }
        )
        cls.half_day_template = cls.AttendanceTemplate.create(
            {
                "name": "Half-day saturday",
                "hour_from": 8,
                "hour_to": 12.5,
                "day_period": "morning",
                "schedule_group_ids": [(6, 0, [cls.schedule_group_0.id])],
            }
        )
        cls.flex_workday_template = cls.AttendanceTemplate.create(
            {
                "name": "Flex Workday",
                "shift_type": "flex",
                "hour_from": 6,
                "hour_to": 20,
                "flex_core_from": 11,
                "flex_core_to": 15,
                "flex_scheduled_hrs": 8,
                "day_period": "8day",
                "schedule_group_ids": [(6, 0, [cls.schedule_group_3.id])],
            }
        )
        cls.att_template_12hr_night = cls.AttendanceTemplate.create(
            {
                "name": "12 Hour Night",
                "hour_from": 18,
                "hour_to": 6,
                "day_period": "evening",
                "span_midnight": True,
            }
        )
        cls.att_template_12hr_day = cls.AttendanceTemplate.create(
            {
                "name": "12 Hour Day",
                "hour_from": 6,
                "hour_to": 18,
                "day_period": "12day",
            }
        )

        # 44Hr Week Calendar
        cls.office_calendar = cls.Calendar.create(
            {
                "name": "44 Hour/Week",
                "attendance_ids": [
                    (0, 0, {"dayofweek": "0", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "1", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "2", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "3", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "4", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "5", "template_id": cls.half_day_template.id}),
                ],
            }
        )

        # Full-week (56Hr) Calendar
        cls.seven_day_calendar = cls.Calendar.create(
            {
                "name": "Full week schedule",
                "dayoff_type": "fix_one",
                "attendance_ids": [
                    (0, 0, {"dayofweek": "0", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "1", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "2", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "3", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "4", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "5", "template_id": cls.att_template.id}),
                    (0, 0, {"dayofweek": "6", "template_id": cls.att_template.id}),
                ],
                "default_dayoff_ids": [
                    (6, 0, [cls.env.ref("resource_schedule.wd_sun").id])
                ],
            }
        )

        # Dupont calendar
        cls.dupont_calendar = cls.Calendar.create(
            {
                "name": "Dupont Schedule",
                "dayoff_type": "fix_all",
                "two_weeks_calendar": True,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "dayofweek": "0",
                            "name": "First Week",
                            "hour_from": 0,
                            "hour_to": 0,
                            "display_type": "line_section",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 11,
                            "dayofweek": "0",
                            "template_id": cls.att_template_12hr_night.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 12,
                            "dayofweek": "1",
                            "template_id": cls.att_template_12hr_night.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 13,
                            "dayofweek": "2",
                            "template_id": cls.att_template_12hr_night.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 14,
                            "dayofweek": "3",
                            "template_id": cls.att_template_12hr_night.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 20,
                            "dayofweek": "0",
                            "name": "Second Week",
                            "hour_from": 0,
                            "hour_to": 0,
                            "display_type": "line_section",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 21,
                            "dayofweek": "0",
                            "template_id": cls.att_template_12hr_day.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 22,
                            "dayofweek": "1",
                            "template_id": cls.att_template_12hr_day.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 23,
                            "dayofweek": "2",
                            "template_id": cls.att_template_12hr_day.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 24,
                            "dayofweek": "4",
                            "template_id": cls.att_template_12hr_night.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 25,
                            "dayofweek": "5",
                            "template_id": cls.att_template_12hr_night.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 26,
                            "dayofweek": "6",
                            "template_id": cls.att_template_12hr_night.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 30,
                            "dayofweek": "0",
                            "name": "Third Week",
                            "hour_from": 0,
                            "hour_to": 0,
                            "display_type": "line_section",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 31,
                            "dayofweek": "3",
                            "template_id": cls.att_template_12hr_day.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 32,
                            "dayofweek": "4",
                            "template_id": cls.att_template_12hr_day.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 33,
                            "dayofweek": "5",
                            "template_id": cls.att_template_12hr_day.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 34,
                            "dayofweek": "6",
                            "template_id": cls.att_template_12hr_day.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 40,
                            "dayofweek": "0",
                            "name": "Fourth Week",
                            "hour_from": 0,
                            "hour_to": 0,
                            "display_type": "line_section",
                        },
                    ),
                ],
            }
        )

        # Teams
        cls.team_alpha = cls.ScheduleTeam.create(
            {
                "name": "Alpha",
                "color": 2,
                "start_week": 0,
                "resource_calendar_id": cls.dupont_calendar.id,
            }
        )
        cls.team_bravo = cls.ScheduleTeam.create(
            {
                "name": "Bravo",
                "color": 4,
                "start_week": 1,
                "resource_calendar_id": cls.dupont_calendar.id,
            }
        )
        cls.team_charlie = cls.ScheduleTeam.create(
            {
                "name": "Charlie",
                "color": 6,
                "start_week": 2,
                "resource_calendar_id": cls.dupont_calendar.id,
            }
        )
        cls.team_delta = cls.ScheduleTeam.create(
            {
                "name": "Delta",
                "color": 8,
                "start_week": 3,
                "resource_calendar_id": cls.dupont_calendar.id,
            }
        )
