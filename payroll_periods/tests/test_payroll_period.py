# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError
from odoo.tests import common, new_test_user


class TestSchedule(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestSchedule, cls).setUpClass()

        cls.Period = cls.env["hr.payroll.period"]
        cls.Schedule = cls.env["hr.payroll.period.schedule"]
        cls.Run = cls.env["hr.payslip.run"]
        cls.Payslip = cls.env["hr.payslip"]
        cls.Exception = cls.env["hr.payslip.exception"]
        cls.exRuleCrit = cls.env.ref("payroll_periods.payslip_exception_third")
        cls.eeJohn = cls.env["hr.employee"].create({"name": "EE John"})
        cls.eeSally = cls.env["hr.employee"].create({"name": "EE Sally"})
        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="hel",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
            email="ric@example.com",
        )

        cls.rule_commision = cls.env["hr.salary.rule"].create(
            {
                "name": "Commission",
                "code": "COMM",
                "category_id": cls.env.ref("payroll.ALW").id,
                "sequence": 17,
                "amount_select": "code",
                "amount_python_compute": "result = inputs.SALECOM.amount",
            }
        )
        cls.input_commision = cls.env["hr.rule.input"].create(
            {
                "name": "Sales Commission Input",
                "code": "SALECOM",
                "input_id": cls.rule_commision.id,
            }
        )

        cls.pay_struct = cls.env.ref("payroll.structure_base")
        cls.pay_struct.write({"rule_ids": [(4, cls.rule_commision.id)]})

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
        return self.Period.create(
            {
                "name": "Period 1",
                "schedule_id": sched_id,
                "date_start": start,
                "date_end": end,
            }
        )

    def create_contract(
        self, eid, state, kanban_state, start, end=None, trial_end=None, pps_id=None
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
            }
        )

    def apply_end_cron(self):
        self.env.ref(
            "payroll_periods.hr_payroll_period_ended_cron"
        ).method_direct_trigger()

    def test_newly_created_period(self):
        """Newly created period should be in 'open' state"""

        pps = self.create_payroll_schedule("monthly", date.today())
        for pp in pps.pay_period_ids:
            self.assertEqual("open", pp.state)

    def test_state_ended(self):
        """Ended state should have state: ended"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        pp = self.create_payroll_period(pps.id, start, end)

        pp.set_state_ended()
        self.assertEqual("ended", pp.state)

    def test_cron_set_ended(self):
        """Set periods past their end date to state: ended"""

        d = date.today() - relativedelta(year=1)
        start = datetime(d.year, 1, 1)
        pps = self.create_payroll_schedule("monthly", start.date())

        self.apply_end_cron()

        for pp in pps.pay_period_ids:
            self.assertEqual("ended", pp.state)

    def test_is_ended(self):
        """If period is past date_end + max roll-over hours it is ended"""

        dt = datetime.now()
        dtStart = dt - relativedelta(days=10)
        dtEnd = dt - relativedelta(hours=6, seconds=1)
        pps = self.create_payroll_schedule("manual", dtStart.date())
        pp = self.create_payroll_period(pps.id, dtStart, dtEnd)

        self.assertTrue(pp.is_ended())

    def test_is_not_ended(self):
        """If period is *NOT* past date_end + max roll-over hours it has not ended"""

        dt = datetime.now()
        dtStart = dt - relativedelta(days=10)
        dtEnd = dt - relativedelta(hours=5, seconds=55)
        pps = self.create_payroll_schedule("manual", dtStart.date())
        pp = self.create_payroll_period(pps.id, dtStart, dtEnd)

        self.assertFalse(pp.is_ended())

    def test_state_payment(self):
        """Periods in payment stage should have state: ended"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        pp = self.create_payroll_period(pps.id, start, end)

        pp.set_state_payment()
        self.assertEqual("payment", pp.state)

    def test_state_payment_with_unignored_exceptions(self):
        """Periods going to payment stage with *UN*-ignored exceptions should *fail*"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        pp = self.create_payroll_period(pps.id, start, end)
        run = self.Run.create(
            {
                "name": "Run A",
                "date_start": start.date(),
                "date_end": end.date(),
                "period_id": pp.id,
            }
        )
        slip = self.Payslip.create(
            {
                "name": "A Payslip",
                "employee_id": self.eeJohn.id,
                "payslip_run_id": run.id,
            }
        )
        self.Exception.create(
            {
                "name": "Net salary less than 1/3 of GROSS",
                "rule_id": self.exRuleCrit.id,
                "slip_id": slip.id,
            }
        )

        self.assertEqual(1, len(pp.exception_ids))
        with self.assertRaises(ValidationError):
            pp.set_state_payment()

    def test_state_payment_with_ignored_exceptions(self):
        """Periods going to payment stage with ignored exceptions should *succeed*"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        pp = self.create_payroll_period(pps.id, start, end)
        run = self.Run.create(
            {
                "name": "Run A",
                "date_start": start.date(),
                "date_end": end.date(),
                "period_id": pp.id,
            }
        )
        slip = self.Payslip.create(
            {
                "name": "A Payslip",
                "employee_id": self.eeJohn.id,
                "payslip_run_id": run.id,
            }
        )
        self.Exception.create(
            {
                "name": "Net salary less than 1/3 of GROSS",
                "rule_id": self.exRuleCrit.id,
                "slip_id": slip.id,
                "ignore": True,
            }
        )

        self.assertEqual(1, len(pp.exception_ids))
        try:
            pp.set_state_payment()
        except ValidationError:
            self.fail("An unexpected Exception was raised")
        self.assertEqual("payment", pp.state)

    def test_create_payslip_dates(self):
        """Payslip date_from -> date_to = same as payroll period"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        self.create_contract(self.eeJohn.id, "draft", "done", start)
        pps = self.create_payroll_schedule("manual", start.date())
        pp = self.create_payroll_period(pps.id, start, end)
        run = self.Run.create(
            {
                "name": "Run A",
                "date_start": start.date(),
                "date_end": end.date(),
                "period_id": pp.id,
            }
        )
        slip = pp.create_payslip(self.eeJohn.id, run_id=run.id)

        self.assertEqual(pp.date_start.date(), slip.date_from)
        self.assertEqual(pp.date_end.date(), slip.date_to)

    def test_create_payslip_dates_two_contract(self):
        """Payslip with 2 contracts: date_from -> date_to = sum of both"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        c2End = start + relativedelta(days=20)
        self.create_contract(
            self.eeJohn.id, "close", "normal", start, start + relativedelta(days=10)
        )
        self.create_contract(
            self.eeJohn.id, "draft", "done", start + relativedelta(days=11), c2End
        )
        pps = self.create_payroll_schedule("manual", start.date())
        pp = self.create_payroll_period(pps.id, start, end)
        run = self.Run.create(
            {
                "name": "Run A",
                "date_start": start.date(),
                "date_end": end.date(),
                "period_id": pp.id,
            }
        )
        slip = pp.create_payslip(self.eeJohn.id, run_id=run.id)

        self.assertEqual(pp.date_start.date(), slip.date_from)
        self.assertEqual(c2End.date(), slip.date_to)

    def test_payslip_input_line(self):
        """After creation the payslip contains configured input lines"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        cc = self.create_contract(
            self.eeJohn.id, "draft", "done", start.date(), pps_id=pps.id
        )
        cc.signal_confirm()
        pp = self.create_payroll_period(pps.id, start, end)
        run = self.Run.create(
            {
                "name": "Run A",
                "date_start": start.date(),
                "date_end": end.date(),
                "period_id": pp.id,
            }
        )
        self.assertEqual("open", cc.state)
        self.assertIn(self.rule_commision, cc.struct_id.rule_ids)
        slip = pp.create_payslip(self.eeJohn.id, run_id=run.id)

        payslip_input = self.env["hr.payslip.input"].search(
            [("payslip_id", "=", slip.id)]
        )
        self.assertEqual(cc, slip.contract_id)
        self.assertEqual(1, len(payslip_input))
        self.assertIn("SALECOM", slip.input_line_ids.mapped("code"))

    def test_rerun_payslip(self):
        """Re-running the payslip should create a new payslip and re-compute it"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        cc = self.create_contract(
            self.eeJohn.id, "draft", "done", start.date(), pps_id=pps.id
        )
        cc.signal_confirm()
        pp = self.create_payroll_period(pps.id, start, end)
        run = self.Run.create(
            {
                "name": "Run A",
                "date_start": start.date(),
                "date_end": end.date(),
                "period_id": pp.id,
            }
        )
        slip = pp.create_payslip(self.eeJohn.id, run_id=run.id)
        slip.compute_sheet()
        id_old = slip.id
        self.assertEqual(1, slip.get_salary_line_total("NET"))

        slip = pp.rerun_payslip(slip)

        self.assertEqual(1, slip.get_salary_line_total("NET"))
        self.assertNotEqual(id_old, slip.id)

    def test_run_multiple_payslips(self):
        """Running more than one payslip at a time"""

        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        cc = self.create_contract(
            self.eeJohn.id, "draft", "done", start.date(), pps_id=pps.id
        )
        cc.signal_confirm()
        cc2 = self.create_contract(
            self.eeSally.id, "draft", "done", start.date(), pps_id=pps.id
        )
        cc2.signal_confirm()
        pp = self.create_payroll_period(pps.id, start, end)
        run = self.Run.create(
            {
                "name": "Run A",
                "date_start": start.date(),
                "date_end": end.date(),
                "period_id": pp.id,
            }
        )
        slip = pp.create_payslip(self.eeJohn.id, run_id=run.id)
        slip2 = pp.create_payslip(self.eeSally.id, run_id=run.id)
        slips = slip + slip2
        slips.compute_sheet()

        self.assertEqual(1, slip.get_salary_line_total("NET"))
        self.assertEqual(1, slip2.get_salary_line_total("NET"))
