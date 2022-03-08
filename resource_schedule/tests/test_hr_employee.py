# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.tests import common


class TestHrEmployee(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.HrEmployee = cls.env["hr.employee"]
        cls.ScheduleShift = cls.env["resource.schedule.shift"]

        cls.employee = cls.HrEmployee.create({"name": "John"})
        cls.eeSally = cls.HrEmployee.create({"name": "Sally"})
        cls.default_calendar = cls.env.ref("resource_schedule.resource_calendar_44h")

    def test_create_schedule(self):

        dStart = date.today()
        while dStart.weekday() != 0:
            dStart -= timedelta(days=1)
        dEnd = dStart + timedelta(days=6)
        self.employee.resource_id.calendar_id = self.default_calendar
        self.eeSally.resource_id.calendar_id = self.default_calendar
        employees = self.employee + self.eeSally
        resources = self.employee.resource_id + self.eeSally.resource_id

        shifts = self.ScheduleShift.search([("resource_id", "in", resources.ids)])
        self.assertEqual(len(shifts), 0, "Initially there are no scheduled shifts")

        shifts = employees.create_schedule(dStart, dEnd)
        self.assertEqual(
            shifts.mapped("resource_id"),
            resources,
            "Shifts were scheduled for both employees",
        )
        self.assertEqual(len(shifts), 12, "The correct number of shifts were created")
