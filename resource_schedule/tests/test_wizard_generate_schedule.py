# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.tests import Form, common


class TestWizardGenerateSchedule(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ScheduleShift = cls.env["resource.schedule.shift"]
        cls.Wizard = cls.env["resource.schedule.generate"]

        cls.eeJohn = cls.env["hr.employee"].create({"name": "John"})
        cls.eeSally = cls.env["hr.employee"].create({"name": "Sally"})
        cls.std35_calendar = cls.env.ref("resource.resource_calendar_std_35h")
        cls.eeJohn.resource_id.calendar_id = cls.std35_calendar
        cls.eeSally.resource_id.calendar_id = cls.std35_calendar

    def get_start_end_dates(self, weeks=1):

        total_days = (weeks * 7) - 1
        dStart = date.today()
        while dStart.weekday() != 0:
            dStart -= timedelta(days=1)
        dEnd = dStart + timedelta(days=total_days)
        return dStart, dEnd

    def test_generate_one_employee(self):

        monday = date.today()
        while monday.weekday() > 0:
            monday -= timedelta(days=1)
        sunday = monday + timedelta(days=6)

        # Find a date that is not a monday
        start = date.today()
        while start.weekday() == 0:
            start += timedelta(days=1)
        self.assertNotEqual(start.weekday(), 0, "The start date is not on a monday")

        frmWizard = Form(self.Wizard)
        frmWizard.date_start = start
        self.assertEqual(
            frmWizard.date_start,
            monday,
            "The wizard has modified the start date to be a monday",
        )

        shift_ids = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeJohn.resource_id.id),
                ("day", ">=", monday),
                ("day", "<=", sunday),
            ]
        )
        self.assertEqual(
            len(shift_ids), 0, "The employee does not have any shifts scheduled"
        )

        frmWizard.no_weeks = 1
        frmWizard.employee_ids.add(self.eeJohn)
        wizard = frmWizard.save()
        wizard.generate_schedules()

        shift_ids = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeJohn.resource_id.id),
                ("day", ">=", monday),
                ("day", "<=", sunday),
            ]
        )
        self.assertEqual(
            len(shift_ids), 10, "The employee has shifts scheduled in the week"
        )

        nextSunday = sunday + timedelta(days=7)
        frmWiz = Form(self.Wizard)
        frmWiz.date_start = monday
        frmWiz.no_weeks = 2
        frmWiz.employee_ids.add(self.eeJohn)
        wizard = frmWiz.save()
        wizard.generate_schedules()

        shift_ids = self.ScheduleShift.search(
            [
                ("resource_id", "=", self.eeJohn.resource_id.id),
                ("day", ">=", monday),
                ("day", "<=", nextSunday),
            ]
        )
        self.assertEqual(
            len(shift_ids),
            20,
            "The employee does not have duplicate shifts for the first week",
        )

    def test_generate_by_calendar(self):

        start, end = self.get_start_end_dates(weeks=2)

        shift_ids = self.ScheduleShift.search(
            [
                (
                    "resource_id",
                    "in",
                    [self.eeJohn.resource_id.id, self.eeSally.resource_id.id],
                ),
                ("day", ">=", start),
                ("day", "<=", end),
            ]
        )
        self.assertEqual(
            len(shift_ids), 0, "The employee does not have any shifts scheduled"
        )

        frmWizard = Form(self.Wizard)
        frmWizard.date_start = start
        frmWizard.no_weeks = 1
        frmWizard.type = "calendar"
        frmWizard.resource_calendar_id = self.std35_calendar
        wizard = frmWizard.save()

        self.assertEqual(
            wizard.employee_ids,
            self.eeJohn | self.eeSally,
            "The wizard automatically loaded the employees attached to the calendar",
        )

        wizard.generate_schedules()

        shift_ids = self.ScheduleShift.search(
            [
                (
                    "resource_id",
                    "in",
                    [self.eeJohn.resource_id.id, self.eeSally.resource_id.id],
                ),
                ("day", ">=", start),
                ("day", "<=", end),
            ]
        )
        self.assertEqual(
            len(shift_ids),
            20,
            "I created one week shift schedule for two employees",
        )
        self.assertEqual(
            shift_ids.mapped("employee_id"),
            self.eeJohn | self.eeSally,
            "I created shift schedule for two employees",
        )
