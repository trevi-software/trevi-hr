# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, common


class TestResourceCalendarAttendance(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.CalendarAttendance = cls.env["resource.calendar.attendance"]
        cls.AttendanceTemplate = cls.env["resource.calendar.attendance.template"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.ScheduleArea = cls.env["resource.schedule.area"]
        cls.ScheduleGroup = cls.env["resource.schedule.group"]

        cls.groupKitchen = cls.ScheduleGroup.create({"name": "Kitchen"})
        cls.areaRestaurant = cls.ScheduleArea.create({"name": "Restaurant"})
        cls.employee = cls.HrEmployee.create({"name": "John"})
        cls.default_calendar = cls.env["resource.calendar"].create({"name": "Std"})
        cls.workday_template = cls.AttendanceTemplate.create(
            {
                "name": "8 - 17 workday",
                "hour_from": 8,
                "hour_to": 17,
                "day_period": "8day",
                "autodeduct_break": True,
                "break_minutes": 60,
            }
        )
        cls.night_template = cls.AttendanceTemplate.create(
            {
                "name": "graveyard shift",
                "hour_from": 22,
                "hour_to": 6,
                "day_period": "evening",
                "span_midnight": True,
            }
        )

    def test_copy_attendance(self):

        catt = self.CalendarAttendance.create(
            {
                "name": "Monday",
                "hour_from": 8,
                "hour_to": 17,
                "calendar_id": self.default_calendar.id,
                "day_period": "8day",
                "template_id": self.night_template.id,
                "span_midnight": True,
                "autopunch": True,
                "default_area_id": self.areaRestaurant.id,
                "schedule_group_ids": [(6, 0, [self.groupKitchen.id])],
            }
        )
        values = catt._copy_attendance_vals()

        self.assertEqual(
            values.get("span_midnight", False),
            True,
            "Field 'span_midnight' is in the list of values to be copied",
        )
        self.assertEqual(
            values.get("autopunch", False),
            True,
            "Field 'autopunch' is in the list of values to be copied",
        )
        self.assertEqual(
            values.get("default_area_id", False),
            self.areaRestaurant.id,
            "Field 'defaul_area_id' is in the list of values to be copied",
        )
        self.assertEqual(
            values.get("schedule_group_ids", False),
            [(6, 0, [self.groupKitchen.id])],
            "Field 'schedule_group_id' is in the list of values to be copied",
        )

    def test_duration(self):

        catt = self.CalendarAttendance.create(
            {
                "name": "Monday",
                "hour_from": 8,
                "hour_to": 17,
                "calendar_id": self.default_calendar.id,
                "day_period": "8day",
            }
        )
        self.assertEqual(
            catt.duration,
            32400,
            "Duration of 8 hour workday without break is 32400 seconds",
        )

    def test_duration_with_break(self):

        catt = self.CalendarAttendance.create(
            {
                "template_id": self.workday_template.id,
                "calendar_id": self.default_calendar.id,
            }
        )
        self.assertEqual(
            catt.duration,
            28800,
            "Duration of 8 hour workday with break is 28800 seconds",
        )

    def test_duration_span_midnight(self):

        catt = self.CalendarAttendance.create(
            {
                "template_id": self.night_template.id,
                "calendar_id": self.default_calendar.id,
            }
        )
        self.assertEqual(
            catt.duration,
            28800,
            "Duration of 8 hour nightshift (no break) is 28800 seconds",
        )

    def test_onchange_template(self):

        frmCA = Form(self.CalendarAttendance)
        self.assertFalse(frmCA.name, "Initialy name field is the default value")
        self.assertEqual(
            frmCA.day_period,
            "morning",
            "Initialy day_period field is the default value",
        )
        self.assertEqual(
            frmCA.hour_from, 0, "Initialy hour_from field is the default value"
        )
        self.assertEqual(
            frmCA.hour_to, 0, "Initialy hour_to field is the default value"
        )

        frmCA.template_id = self.workday_template
        self.assertEqual(
            frmCA.name,
            "8 - 17 workday",
            "After template is set the name equals the template name",
        )
        self.assertEqual(
            frmCA.day_period,
            "8day",
            "After template is set the day_period equals the template name",
        )
        self.assertEqual(
            frmCA.hour_from,
            8,
            "After template is set the hour_from equals the template name",
        )
        self.assertEqual(
            frmCA.hour_to,
            17,
            "After template is set the hour_to equals the template name",
        )

    def test_span_midnight(self):

        catt = self.CalendarAttendance.create(
            {
                "template_id": self.night_template.id,
                "calendar_id": self.default_calendar.id,
            }
        )
        self.assertTrue(catt.span_midnight, "The work detail is marked 'span midnight'")
        self.assertGreater(
            catt.hour_from,
            catt.hour_to,
            "If the start time is greater than the end time",
        )
