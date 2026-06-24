# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
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
        cls.flex_night_template = cls.AttendanceTemplate.create(
            {
                "name": "Night flex shift",
                "shift_type": "flex",
                "hour_from": 18,
                "hour_to": 6,
                "flex_core_from": 0,
                "flex_core_to": 4,
                "day_period": "12night",
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
                "shift_type": "std",
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

        catt.autopunch = False
        catt.shift_type = "flex"
        catt.flex_core_from = 10
        catt.flex_core_to = 15
        catt.flex_scheduled_hrs = 7
        catt.flex_scheduled_avg = True
        catt.flex_weekly_hrs = 35
        values = catt._copy_attendance_vals()
        self.assertEqual(
            values.get("shift_type", False),
            "flex",
            "Field 'shift_type' is in the list of values to be copied",
        )
        self.assertEqual(
            values.get("flex_scheduled_hrs", False),
            7,
            "Field 'flex_scheduled_hrs' is in the list of values to be copied",
        )
        self.assertTrue(
            values.get("flex_scheduled_avg", False),
            "Field 'flex_scheduled_avg' is in the list of values to be copied",
        )
        self.assertEqual(
            values.get("flex_core_from", False),
            10,
            "Field 'flex_core_from' is in the list of values to be copied",
        )
        self.assertEqual(
            values.get("flex_core_to", False),
            15,
            "Field 'flex_core_to' is in the list of values to be copied",
        )
        self.assertEqual(
            values.get("flex_weekly_hrs", False),
            35,
            "Field 'flex_weekly_hrs' is in the list of values to be copied",
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
            "In shifts that span midnight start time is greater than the end time",
        )

        catt = self.CalendarAttendance.create(
            {
                "template_id": self.flex_night_template.id,
                "calendar_id": self.default_calendar.id,
            }
        )
        self.assertTrue(catt.span_midnight, "The work detail is marked 'span midnight'")
        self.assertGreater(
            catt.hour_from,
            catt.hour_to,
            "A flex attendance that spans midnight was successfully created",
        )

    def test_flex_autopunch(self):

        with self.assertRaises(ValidationError):
            self.AttendanceTemplate.create(
                {
                    "name": "Flex Shift w/ Autopunch",
                    "hour_from": 10,
                    "hour_to": 15,
                    "day_period": "8day",
                    "shift_type": "flex",
                    "autopunch": True,
                }
            )

        with self.assertRaises(ValidationError):
            self.CalendarAttendance.create(
                {
                    "name": "Flex Shift w/ Autopunch",
                    "calendar_id": self.default_calendar.id,
                    "hour_from": 10,
                    "hour_to": 15,
                    "day_period": "8day",
                    "shift_type": "flex",
                    "autopunch": True,
                }
            )

        tpl = self.AttendanceTemplate.create(
            {
                "name": "Flex Shift w/ Autopunch",
                "hour_from": 10,
                "hour_to": 15,
                "day_period": "8day",
                "shift_type": "flex",
            }
        )
        with self.assertRaises(ValidationError):
            tpl.autopunch = True

        attendance = self.CalendarAttendance.create(
            {
                "name": "Flex Shift w/ Autopunch",
                "calendar_id": self.default_calendar.id,
                "hour_from": 10,
                "hour_to": 15,
                "day_period": "8day",
                "shift_type": "flex",
            }
        )
        with self.assertRaises(ValidationError):
            attendance.autopunch = True

    def test_flex_template_invalid_values(self):

        frmAtt = Form(self.AttendanceTemplate)
        frmAtt.name = "Flex shift"
        frmAtt.day_period = "8day"
        frmAtt.shift_type = "flex"
        frmAtt.hour_from = 11
        frmAtt.hour_to = 14
        frmAtt.flex_core_from = 10
        frmAtt.flex_core_to = 15
        frmAtt.flex_scheduled_hrs = 25
        tpl = frmAtt.save()

        self.assertEqual(
            tpl.flex_scheduled_hrs,
            24,
            "Invalid value for 'flex_scheduled_hrs' reset to 24",
        )
        self.assertEqual(
            tpl.hour_from,
            10,
            "Invalid value for 'hour_from' resets to 'flex_core_from'",
        )
        self.assertEqual(
            tpl.hour_to, 15, "Invalid value for 'hour_to' resets to 'flex_cre_to'"
        )

        frmTpl = Form(self.AttendanceTemplate)
        frmTpl.name = "Flex shift"
        frmTpl.day_period = "8day"
        frmTpl.shift_type = "flex"
        frmTpl.hour_from = 8
        frmTpl.hour_to = 17
        frmTpl.flex_core_from = 0
        frmTpl.flex_core_to = 0
        frmTpl.flex_scheduled_hrs = -1
        tpl = frmTpl.save()
        self.assertEqual(
            tpl.flex_scheduled_hrs,
            0,
            "Invalid value for 'flex_scheduled_hrs' reset to 0",
        )
        self.assertEqual(
            tpl.flex_core_from,
            0,
            "Value 0 for 'flex_core_from' means core hours are not mandatory",
        )
        self.assertEqual(
            tpl.flex_core_to,
            0,
            "Value 0 for 'flex_core_to' means core hours are not mandatory",
        )

        frmTpl = Form(self.AttendanceTemplate)
        frmTpl.name = "Flex shift"
        frmTpl.day_period = "8day"
        frmTpl.shift_type = "flex"
        frmTpl.hour_from = 8
        frmTpl.hour_to = 17
        frmTpl.flex_core_from = 12
        frmTpl.flex_core_to = 8
        tpl = frmTpl.save()

        self.assertEqual(
            tpl.flex_core_to,
            12,
            "If too small, 'flex_core_to' is reset to the value of 'flex_core_from'",
        )

    def test_flex_invalid_values(self):

        frmAtt = Form(self.CalendarAttendance)
        frmAtt.calendar_id = self.default_calendar
        frmAtt.name = "Flex shift"
        frmAtt.day_period = "8day"
        frmAtt.shift_type = "flex"
        frmAtt.hour_from = 11
        frmAtt.hour_to = 14
        frmAtt.flex_core_from = 10
        frmAtt.flex_core_to = 15
        frmAtt.flex_scheduled_hrs = 25
        att = frmAtt.save()

        self.assertEqual(
            att.flex_scheduled_hrs,
            24,
            "Invalid value for 'flex_scheduled_hrs' reset to 24",
        )
        self.assertEqual(
            att.hour_from,
            10,
            "Invalid value for 'hour_from' resets to 'flex_core_from'",
        )
        self.assertEqual(
            att.hour_to, 15, "Invalid value for 'hour_to' resets to 'flex_core_to'"
        )

        frmAtt = Form(self.CalendarAttendance)
        frmAtt.calendar_id = self.default_calendar
        frmAtt.name = "Flex shift"
        frmAtt.day_period = "8day"
        frmAtt.shift_type = "flex"
        frmAtt.hour_from = 8
        frmAtt.hour_to = 17
        frmAtt.flex_core_from = 0
        frmAtt.flex_core_to = 0
        frmAtt.flex_scheduled_hrs = -1
        att = frmAtt.save()

        self.assertEqual(
            att.flex_scheduled_hrs,
            0,
            "Invalid value for 'flex_scheduled_hrs' reset to 0",
        )
        self.assertEqual(
            att.flex_core_from,
            0,
            "Value 0 for 'flex_core_from' means core hours are not mandatory",
        )
        self.assertEqual(
            att.flex_core_to,
            0,
            "Value 0 for 'flex_core_to' means core hours are not mandatory",
        )
