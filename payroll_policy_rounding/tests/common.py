# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from pytz import timezone, utc

from odoo.tests import common, new_test_user


class TestPolicyCommon(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPolicyCommon, cls).setUpClass()

        cls.HrAttendance = cls.env["hr.attendance"]
        cls.HrContract = cls.env["hr.contract"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.PolicyGroup = cls.env["hr.policy.group"]
        cls.Policy = cls.env["hr.policy.rounding"]
        cls.PolicyLine = cls.env["hr.policy.line.rounding"]
        cls.policy = cls.Policy.create(
            {"name": "ROUNDING POLICY1", "date": date.today(), "tz": "UTC"}
        )
        cls.line = cls.PolicyLine.create(
            {
                "attendance_type": "in",
                "round_type": "avg",
                "policy_id": cls.policy.id,
            }
        )
        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="pm",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
            email="pm@example.com",
        )
        # Payroll user
        cls.userPU = new_test_user(
            cls.env,
            login="pu",
            groups="base.group_user,payroll.group_payroll_user",
            name="Payroll manager",
            email="pu@example.com",
        )
        # HR Manager
        cls.userHRM = new_test_user(
            cls.env,
            login="hrm",
            groups="base.group_user,hr.group_hr_manager",
            name="Payroll manager",
            email="hrm@example.com",
        )

        # Employee with contract
        cls.test_employee = cls.HrEmployee.create({"name": "Test Employee"})
        cls.test_contract = cls.create_contract(cls)
        cls.apply_contract_cron(cls)

    def create_contract(
        self, eid=None, state="draft", kanban_state="done", start=None, end=None
    ):
        if eid is None:
            eid = self.test_employee.id
        if start is None:
            start = date.today()
        return self.HrContract.create(
            {
                "name": "Contract",
                "employee_id": eid,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "date_end": end,
            }
        )

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def make_datetime(self, d: date, sTime: str) -> datetime:
        return datetime.combine(d, datetime.strptime(sTime, "%H:%M").time())

    def get_start_end_dates(self, weeks=1):

        total_days = (weeks * 7) - 1
        dStart = date.today()
        while dStart.weekday() != 0:
            dStart -= timedelta(days=1)
        dEnd = dStart + timedelta(days=total_days)
        return dStart, dEnd

    def localize_dt(self, dt, tz, reverse=False):
        """
        Localize naive dt from database (UTC) to timzezone tz. If reverse is True
        a naive dt that is in timezone tz is converted to naive dt for storage in db.
        """

        local_tz = timezone(tz)
        if reverse:
            res = (
                local_tz.localize(dt, is_dst=False).astimezone(utc).replace(tzinfo=None)
            )
        else:
            res = utc.localize(dt, is_dst=False).astimezone(local_tz)
        return res

    def setup_pg(self, line_ids, tz="UTC"):

        p = self.Policy.create(
            {
                "name": "P1",
                "date": date.today(),
                "tz": tz,
                "line_ids": line_ids,
            }
        )
        pg = self.PolicyGroup.create(
            {
                "name": "PGroup",
                "rounding_policy_ids": [(6, 0, [p.id])],
            }
        )
        self.test_contract.policy_group_id = pg

        self.assertGreater(
            len(self.test_employee.resource_id.scheduled_shift_ids),
            0,
            "Shifts have been created on contract creation",
        )

        return (p, pg)

    def set_in_times(self, strClock, strCheck):
        clock_in = self.localize_dt(
            self.make_datetime(date.today(), strClock),
            self.test_employee.resource_id.tz,
            reverse=True,
        )
        check_in = self.localize_dt(
            self.make_datetime(date.today(), strCheck),
            self.test_employee.resource_id.tz,
            reverse=True,
        )
        return (clock_in, check_in)

    def set_out_times(self, strIn, strClock, strCheck):
        check_in = self.localize_dt(
            self.make_datetime(date.today(), strIn),
            self.test_employee.resource_id.tz,
            reverse=True,
        )
        clock_out = self.localize_dt(
            self.make_datetime(date.today(), strClock),
            self.test_employee.resource_id.tz,
            reverse=True,
        )
        check_out = self.localize_dt(
            self.make_datetime(date.today(), strCheck),
            self.test_employee.resource_id.tz,
            reverse=True,
        )
        return (check_in, clock_out, check_out)
