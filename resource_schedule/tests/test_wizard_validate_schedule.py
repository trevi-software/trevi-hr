# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.tests import Form, common


class TestWizardValidateSchedule(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ScheduleShift = cls.env["resource.schedule.shift"]
        cls.Wizard = cls.env["resource.schedule.validate.departments"]

        cls.dep_management = cls.env.ref("hr.dep_management")
        cls.eeJohn = cls.env["hr.employee"].create(
            {"name": "John", "department_id": cls.dep_management.id}
        )
        cls.std35_calendar = cls.env.ref("resource.resource_calendar_std_35h")
        cls.eeJohn.resource_id.calendar_id = cls.std35_calendar

    def get_start_end_dates(self, weeks=1):

        total_days = (weeks * 7) - 1
        dStart = date.today()
        while dStart.weekday() != 0:
            dStart -= timedelta(days=1)
        dEnd = dStart + timedelta(days=total_days)
        return dStart, dEnd

    def test_validate_department(self):

        start, end = self.get_start_end_dates()
        shifts = self.eeJohn.create_schedule(start, end)
        for shift in shifts:
            self.assertFalse(shift.published, "Initially all shifts are unpublished")

        frmWizard = Form(self.Wizard)
        frmWizard.department_ids.add(self.dep_management)
        wizard = frmWizard.save()
        wizard.do_validate()
        for shift in shifts:
            self.assertTrue(shift.published, "All shifts of the employee are published")
