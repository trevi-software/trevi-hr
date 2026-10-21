# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from .common import TestResourceScheduleCommon


class TestContract(TestResourceScheduleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrVersion = cls.env["hr.version"]
        # Odoo 19 gives every employee a version dated today, and hr.version
        # enforces a unique (employee_id, date_version). Backdate the employee's
        # initial version so the contract versions created below (dated today)
        # are the employee's *current* version - otherwise their computed
        # date_end is capped to yesterday and the module treats the contract as
        # being in the past.
        cls.employee = cls.HrEmployee.create(
            {"name": "John", "date_version": "2000-01-01"}
        )
        cls.empty_calendar = cls.env["resource.calendar"].create(
            {
                "name": "Standard 0 hours/week",
            }
        )
        cls.empty_calendar.attendance_ids.unlink()
        cls.default_calendar = cls.office_calendar

    def create_contract(
        self,
        employee_id=None,
        start=None,
        end=None,
        trial_end=None,
        wage=1,
        calendar_id=None,
        date_version=None,
    ):
        if employee_id is None:
            employee_id = self.employee.id
        if start is None:
            start = date.today()
        if calendar_id is None:
            calendar_id = self.default_calendar.id

        res = {
            "name": "Contract",
            "employee_id": employee_id,
            "wage": wage,
            # 19.0 enforces a unique (employee_id, date_version) index; the
            # employee's initial version is backdated in setUpClass, so the
            # contract version can be dated today and still be the current one.
            "date_version": date_version or date.today(),
            "contract_date_start": start,
            "trial_date_end": trial_end,
            "contract_date_end": end,
            "resource_calendar_id": calendar_id,
        }

        return self.env["hr.version"].create(res)

    def test_no_work_detail(self):
        c = self.create_contract(calendar_id=self.empty_calendar.id)

        self.assertEqual(
            len(c.resource_calendar_id.attendance_ids),
            0,
            "The contract has no Work Details",
        )
        self.assertEqual(
            len(c.employee_id.resource_id.scheduled_shift_ids),
            0,
            "No shifts created because the work item doesn't have work details",
        )

    def test_contract_in_past(self):
        prev_start = date(2021, 1, 1)
        prev_end = date(2021, 1, 31)
        c = self.create_contract(
            start=prev_start, end=prev_end, calendar_id=self.default_calendar.id
        )

        self.assertEqual(
            len(c.employee_id.resource_id.scheduled_shift_ids),
            0,
            "No shifts are created for contracts in the past",
        )

    def test_multiple_contracts(self):
        prev_start = date.today()
        prev_end = prev_start + relativedelta(days=31)
        start = prev_start + relativedelta(days=32)
        c = self.create_contract(
            start=prev_start, end=prev_end, calendar_id=self.default_calendar.id
        )
        first_shift_ids = c.employee_id.resource_id.scheduled_shift_ids

        self.assertEqual(
            c.resource_calendar_id,
            self.default_calendar,
            "The calendar on the contract is the default calendar",
        )
        self.assertEqual(
            c.employee_id.resource_id.calendar_id,
            self.default_calendar,
            "The calendar on the employee resource is the default calendar",
        )
        self.assertGreater(
            len(first_shift_ids), 0, "Shifts have been created for first contract"
        )

        c = self.create_contract(
            start=start,
            calendar_id=self.default_calendar.id,
            date_version=start,
        )
        curr_shift_ids = c.employee_id.resource_id.scheduled_shift_ids
        self.assertEqual(
            len(first_shift_ids),
            len(curr_shift_ids),
            "Length of shifts after second contract is the same as before it",
        )
        self.assertEqual(
            first_shift_ids,
            curr_shift_ids,
            "Shifts after second contract are the same as those after the first",
        )

    def test_schedule_on_create(self):
        c = self.create_contract(calendar_id=self.empty_calendar.id)
        self.assertEqual(
            c.employee_id.resource_id.calendar_id,
            self.empty_calendar,
            "Setting calendar during contract creation sets calendar on resource",
        )

    def test_write_new_schedule(self):
        c = self.create_contract(calendar_id=self.empty_calendar.id)
        self.assertEqual(
            c.employee_id.resource_id.calendar_id,
            self.empty_calendar,
            "The initial calender is set",
        )

        c.resource_calendar_id = self.default_calendar
        self.assertEqual(
            c.employee_id.resource_id.calendar_id,
            self.default_calendar,
            "Changing calendar on the contract changes calendar on the resource",
        )

    def test_schedule_on_first_contract(self):
        c = self.create_contract(calendar_id=self.default_calendar.id)

        i = 0
        for attendance in c.resource_calendar_id.attendance_ids:
            shift = c.employee_id.resource_id.scheduled_shift_ids[i]
            self.assertEqual(
                shift.hour_from,
                attendance.hour_from,
                "Start hour scheduled shift equals start hour on work detail",
            )
            self.assertEqual(
                shift.hour_to,
                attendance.hour_to,
                "End hour on scheduled shift equals end hour on work detail",
            )

            i += 1