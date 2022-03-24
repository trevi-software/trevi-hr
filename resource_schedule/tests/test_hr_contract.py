# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestContract(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestContract, cls).setUpClass()

        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.employee = cls.HrEmployee.create({"name": "John"})
        cls.default_calendar = cls.env.ref("resource_schedule.resource_calendar_44h")
        cls.empty_calendar = cls.env["resource.calendar"].create(
            {
                "name": "Standard 0 hours/week",
            }
        )
        cls.empty_calendar.attendance_ids.unlink()

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
        if calendar_id is None:
            calendar_id = self.default_calendar.id

        res = {
            "name": "Contract",
            "employee_id": employee_id,
            "state": state,
            "kanban_state": kanban_state,
            "wage": wage,
            "date_start": start,
            "trial_date_end": trial_end,
            "date_end": end,
            "resource_calendar_id": calendar_id,
        }

        return self.env["hr.contract"].create(res)

    def apply_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def test_no_work_detail(self):

        c = self.create_contract(calendar_id=self.empty_calendar.id)
        self.apply_cron()

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
        self.apply_cron()

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

        c = self.create_contract(start=start, calendar_id=self.default_calendar.id)
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
