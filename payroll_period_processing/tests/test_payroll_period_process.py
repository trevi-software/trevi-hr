# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from pytz import timezone, utc

from odoo.tests import common, new_test_user

from odoo.addons.mail.tests.common import mail_new_test_user


class TestProcessing(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestProcessing, cls).setUpClass()

        cls.Wizard = cls.env["hr.payroll.processing"]
        cls.Period = cls.env["hr.payroll.period"]
        cls.Schedule = cls.env["hr.payroll.period.schedule"]
        cls.HolidayPublic = cls.env["hr.holidays.public"]
        cls.HolidayPublicLine = cls.env["hr.holidays.public.line"]
        cls.Department = cls.env["hr.department"].with_context(tracking_disable=True)
        cls.LeaveType = cls.env["hr.leave.type"].with_context(tracking_disable=True)
        cls.payrollOfficer = new_test_user(
            cls.env,
            login="Payroff",
            groups="base.group_user,payroll.group_payroll_user",
            name="Pyaroll Officer",
            email="payroff@example.com",
        )
        cls.pay_struct = cls.env.ref("payroll.structure_base")
        cls.rd_dept = cls.Department.create(
            {
                "name": "Research and devlopment",
            }
        )
        cls.job_ux_designer = cls.env["hr.job"].create(
            {
                "name": "#UX Designer",
                "department_id": cls.rd_dept.id,
            }
        )

        # Employee
        #
        cls.user_employee = mail_new_test_user(
            cls.env, login="david", groups="base.group_user"
        )
        cls.employee_emp = cls.env["hr.employee"].create(
            {
                "name": "David Employee",
                "user_id": cls.user_employee.id,
                "department_id": cls.rd_dept.id,
            }
        )

        # Leave
        #
        cls.leave_type_1 = cls.LeaveType.create(
            {
                "name": "NotLimitedHR",
                "allocation_type": "no",
                "leave_validation_type": "hr",
                "validity_start": False,
            }
        )
        cls.employee_leave = cls.env["hr.leave"].create(
            {
                "name": "Hol11",
                "employee_id": cls.employee_emp.id,
                "holiday_status_id": cls.leave_type_1.id,
                "date_from": datetime(2021, 9, 1),
                "date_to": datetime(2021, 9, 3),
                "number_of_days": 2,
            }
        )

        # Public Holiday related
        #
        cls.hrMgr = new_test_user(
            cls.env,
            login="hel",
            groups="base.group_user,hr_holidays.group_hr_holidays_manager",
            name="HR Officer",
            email="ric@example.com",
        )
        cls.new_year = date(2021, 9, 11)
        cls.holidays = cls.HolidayPublic.with_user(cls.hrMgr).create({"year": 2021})
        cls.holidayLine = cls.HolidayPublicLine.with_user(cls.hrMgr).create(
            [
                {
                    "name": "New Year",
                    "date": cls.new_year,
                    "variable_date": False,
                    "year_id": cls.holidays.id,
                },
            ]
        )

    def create_payroll_schedule(self, stype=False, initial_date=False):
        return self.Schedule.create(
            {
                "name": "PPS",
                "tz": "Africa/Addis_Ababa",
                "type": stype,
                "initial_period_date": initial_date,
            }
        )

    def create_payroll_period(self, sched_id, start, end):
        local_tz = timezone("Africa/Addis_Ababa")
        tzdt_start = local_tz.localize(start)
        utcdt_start = tzdt_start.astimezone(utc)
        tzdt_end = local_tz.localize(end)
        utcdt_end = tzdt_end.astimezone(utc)
        return self.Period.create(
            {
                "name": "Period 1",
                "schedule_id": sched_id,
                "date_start": utcdt_start.replace(tzinfo=None),
                "date_end": utcdt_end.replace(tzinfo=None),
            }
        )

    def create_contract(
        self,
        eid,
        state,
        kanban_state,
        start,
        end=None,
        trial_end=None,
        pps_id=None,
        job_id=False,
    ):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": eid,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
                "struct_id": self.pay_struct.id,
                "pps_id": pps_id,
                "job_id": job_id,
            }
        )

    def setUpCommon(self):

        # Payroll Period
        #
        start = datetime(2021, 9, 1)
        end = datetime(2021, 9, 30, 23, 59, 59)
        self.schedule = self.create_payroll_schedule("manual", start.date())
        self.period = self.create_payroll_period(self.schedule.id, start, end)
        self.period.set_state_ended()

    def test_load_public_holidays(self):
        """When in 'holidays' state the list of public holidays is populated"""

        self.setUpCommon()
        wiz = (
            self.Wizard.with_user(self.payrollOfficer)
            .with_context({"active_id": self.period.id})
            .create({})
        )
        wiz.state_holidays()
        self.assertIn(self.holidayLine, wiz.public_holiday_ids)

    def test_load_leaves(self):
        """When in 'apprvlv' state the list of draft leaves is populated"""

        self.setUpCommon()
        wiz = (
            self.Wizard.with_user(self.payrollOfficer)
            .with_context({"active_id": self.period.id})
            .create({})
        )
        wiz.state_leaves()
        self.assertEqual("confirm", self.employee_leave.state)
        self.assertIn(self.employee_leave, wiz.leave_ids)

    def test_load_contracts(self):
        """When the wizard loads the list of un-approved contracts is populated"""

        self.setUpCommon()
        start = datetime(2021, 9, 1)
        cc = self.create_contract(self.employee_emp.id, "draft", "done", start)
        wiz = (
            self.Wizard.with_user(self.payrollOfficer)
            .with_context({"active_id": self.period.id})
            .create({})
        )

        self.assertIn(cc, wiz.contract_ids)

    def test_payroll_register_create(self):
        """Payroll register, batch run and payslip creation"""

        self.setUpCommon()
        start = datetime(2021, 9, 1)
        cc = self.create_contract(
            self.employee_emp.id,
            "draft",
            "done",
            start.date(),
            pps_id=self.schedule.id,
            job_id=self.job_ux_designer.id,
        )
        cc.signal_confirm()
        wiz = (
            self.Wizard.with_user(self.payrollOfficer)
            .with_context({"active_id": self.period.id})
            .create({})
        )
        wiz.create_payroll_register()

        register = self.period.register_id
        self.assertEqual(self.job_ux_designer, self.employee_emp.job_id)
        self.assertEqual(self.rd_dept, self.employee_emp.department_id)
        self.assertEqual(self.rd_dept, cc.department_id)
        self.assertEqual(self.period.date_start, register.date_start)
        self.assertEqual(self.period.date_end, register.date_end)
        self.assertGreater(len(register.run_ids), 0)
        departments = register.run_ids.mapped("department_ids")
        self.assertIn(self.rd_dept, departments)
        fail = True
        for run in register.run_ids:
            self.assertEqual(run.period_id, self.period)
            if self.rd_dept in run.department_ids:
                employees = run.slip_ids.mapped("employee_id")
                self.assertIn(self.employee_emp, employees)
                fail = False
                break
        if fail:
            self.assertFail("Unable to find department in payslip batches")

    def test_payslip_tz_date_start(self):
        """Payroll batch run and payslip start/end dates"""

        self.setUpCommon()
        start = datetime(2021, 9, 1)
        utc_start_dt = datetime(2021, 8, 31, 21, 0, 0)
        cc = self.create_contract(
            self.employee_emp.id,
            "draft",
            "done",
            start.date(),
            pps_id=self.schedule.id,
            job_id=self.job_ux_designer.id,
        )
        cc.signal_confirm()
        wiz = (
            self.Wizard.with_user(self.payrollOfficer)
            .with_context({"active_id": self.period.id})
            .create({})
        )
        wiz.create_payroll_register()

        register = self.period.register_id
        self.assertEqual(self.period.date_start, register.date_start)
        self.assertEqual(self.period.date_end, register.date_end)
        self.assertGreater(len(register.run_ids), 0)

        self.assertEqual(
            self.period.date_start,
            utc_start_dt,
            "Payroll Period start datetime is in UTC",
        )
        self.assertEqual(
            register.date_start,
            utc_start_dt,
            "Payroll Register start datetime is in UTC",
        )
        self.assertEqual(
            register.run_ids[0].date_start,
            start.date(),
            "Start date of payslip batch is adjusted for timezone",
        )
