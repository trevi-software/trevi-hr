# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, common


class TestResourceCalenar(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ResourceCalendar = cls.env["resource.calendar"]
        cls.wtpl_morning = cls.env.ref("resource_schedule.attendance_template_0")
        cls.wtpl_afternoon = cls.env.ref("resource_schedule.attendance_template_1")
        cls.wtpl_weekday = cls.env.ref("resource_schedule.attendance_template_demo0")
        cls.wtpl_flex_weekday = cls.env.ref(
            "resource_schedule.attendance_template_demo11"
        )
        cls.default_calendar = cls.env.ref("resource_schedule.resource_calendar_44h")
        cls.production_calendar = cls.env.ref("resource_schedule.resource_calendar_56h")

    def test_default_get(self):

        cal = self.ResourceCalendar.create({"name": "My Work Cal"})
        self.assertGreater(
            len(cal.attendance_ids), 0, "The new calendar has default work days"
        )
        for att in cal.attendance_ids.sorted("sequence"):
            self.assertIn(
                att.day_period,
                ["morning", "afternoon"],
                "The default workday has a day period of 'morning' or 'afternoon'",
            )
            if att.day_period == "morning":
                self.assertEqual(
                    att.template_id,
                    self.wtpl_morning,
                    "The 'morning' default workday has a template attached",
                )
            elif att.day_period == "afternoon":
                self.assertEqual(
                    att.template_id,
                    self.wtpl_afternoon,
                    "The 'afternoon' default workday has a template attached",
                )

    def test_default_get2(self):

        company = self.env["res.company"].create({"name": "Company 2"})
        cal = company.resource_calendar_id
        self.assertGreater(
            len(cal.attendance_ids), 0, "The new calendar has default work days"
        )
        for att in cal.attendance_ids:
            self.assertIn(
                att.day_period,
                ["morning", "afternoon"],
                "The default workday has a day period of 'morning' or 'afternoon'",
            )
            if att.day_period == "morning":
                self.assertEqual(
                    att.template_id,
                    self.wtpl_morning,
                    "The 'morning' default workday has a template attached",
                )
            elif att.day_period == "afternoon":
                self.assertEqual(
                    att.template_id,
                    self.wtpl_afternoon,
                    "The 'afternoon' default workday has a template attached",
                )

    def test_field_two_weeks_calendar(self):

        self.assertEqual(
            len(
                self.default_calendar.attendance_ids.filtered(
                    lambda att: att.display_type == "line_section"
                )
            ),
            0,
            "Initially there is only one week in the work item",
        )
        self.assertFalse(
            self.default_calendar.two_weeks_calendar,
            "When there is only one week the field 'two_weeks_calendar' is False",
        )

        self.default_calendar.switch_calendar_type()
        with Form(self.default_calendar) as frmCalendar:
            with frmCalendar.attendance_ids.new() as line:
                line.name = "Week 3"
                line.display_type = "line_section"

        self.assertEqual(
            len(
                self.default_calendar.attendance_ids.filtered(
                    lambda att: att.display_type == "line_section"
                )
            ),
            3,
            "There is more than one week in the work item",
        )
        self.assertTrue(
            self.default_calendar.two_weeks_calendar,
            "When there is more than one week the field 'two_weeks_calendar' is True",
        )

    def test_field_multi_calendar_change_sequence(self):

        self.assertEqual(
            len(
                self.default_calendar.attendance_ids.filtered(
                    lambda att: att.display_type == "line_section"
                )
            ),
            0,
            "Initially there is only one week in the work item",
        )

        self.default_calendar.switch_calendar_type()
        with Form(self.default_calendar) as frmCalendar:
            with frmCalendar.attendance_ids.new() as line:
                line.template_id = self.wtpl_morning
                line.dayofweek = "5"
                line.sequence = 36
        last_day = self.default_calendar.attendance_ids.sorted("sequence")[-1]
        last_section = self.default_calendar.attendance_ids.filtered(
            lambda a: a.display_type == "line_section"
        )[-1]
        self.assertEqual(
            last_day.dayofweek, "5", "The last day of the calendar is saturday"
        )
        self.assertEqual(
            last_day.week_type, "1", "The week type of the last day is 'Odd Week'"
        )
        self.assertEqual(
            last_day.sequence,
            36,
            "The last day of the calendar is the value I just inserted",
        )
        self.assertEqual(last_section.sequence, 25, "I found the last section")

        last_day.sequence = 25
        self.assertEqual(
            last_day.week_nbr,
            0,
            "The week nbr of the last day has moved into the previous week",
        )
        self.assertEqual(
            last_day.week_type,
            "0",
            "The week type of the last day has changed to 'Even Week'",
        )

    def test_compute_hours_per_day(self):

        self.default_calendar.switch_calendar_type()
        self.assertEqual(
            len(
                self.default_calendar.attendance_ids.filtered(
                    lambda att: att.display_type == "line_section"
                )
            ),
            2,
            "Initially there are two weeks in the calendar",
        )
        self.assertEqual(
            self.default_calendar.hours_per_day,
            8,
            "Initially, calender working hours average 8 hrs/day",
        )
        hours_per_day = self.default_calendar.hours_per_day

        with Form(self.default_calendar) as frmCalendar:
            with frmCalendar.attendance_ids.new() as line:
                line.name = "Week 3"
                line.display_type = "line_section"
                line.dayofweek = "0"
                line.sequence = 40
                line.hour_from = 0
                line.hour_to = 0
            sequence = 41
            for idx in range(5):
                with frmCalendar.attendance_ids.new() as line:
                    line.template_id = self.wtpl_morning
                    line.dayofweek = str(idx)
                    line.sequence = sequence
                with frmCalendar.attendance_ids.new() as line:
                    line.template_id = self.wtpl_afternoon
                    line.dayofweek = str(idx)
                    line.sequence = sequence + 1
                sequence += 2
        self.assertEqual(
            len(
                self.default_calendar.attendance_ids.filtered(
                    lambda att: att.display_type == "line_section"
                )
            ),
            3,
            "I have added a third week to the calendar",
        )
        self.assertEqual(
            len(
                self.default_calendar.attendance_ids.filtered(
                    lambda att: att.display_type is False and att.week_nbr == 2
                )
            ),
            10,
            "I have added 5 working days to the calendar",
        )

        self.assertEqual(
            self.default_calendar.hours_per_day,
            hours_per_day,
            "After additional week calender working hours still average 8 hrs/day",
        )

    def test_hours_per_day_autodeduct_break(self):

        cal = self.default_calendar.copy()
        # cal.switch_calendar_type()
        cal.attendance_ids.unlink()
        with Form(cal) as frmCalendar:
            for idx in range(5):
                with frmCalendar.attendance_ids.new() as line:
                    line.template_id = self.wtpl_weekday
                    line.dayofweek = str(idx)
                    line.sequence = 41 + idx

        self.assertEqual(
            cal.hours_per_day, 8, "Average hours/day correctly deducts break time"
        )

    def test_flex_hours_per_day(self):

        cal = self.default_calendar.copy()
        cal.attendance_ids.unlink()
        self.wtpl_flex_weekday.flex_scheduled_hrs = 8
        with Form(cal) as frmCalendar:
            for idx in range(5):
                with frmCalendar.attendance_ids.new() as line:
                    line.template_id = self.wtpl_flex_weekday
                    line.dayofweek = str(idx)
        self.assertEqual(
            cal.hours_per_day, 8, "Average hours/day equals flex scheduled hours"
        )
