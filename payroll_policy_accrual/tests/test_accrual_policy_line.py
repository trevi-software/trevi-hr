# Copyright (C) 2021 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common


class TestAccrualPolicy(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccrualPolicy, cls).setUpClass()

        cls.PolicyGroup = cls.env["hr.policy.group"]
        cls.Policy = cls.env["hr.policy.accrual"]
        cls.PolicyLine = cls.env["hr.policy.line.accrual"]
        cls.AccrualJob = cls.env["hr.policy.line.accrual.job"]
        cls.Accrual = cls.env["hr.accrual"]
        cls.Employee = cls.env["hr.employee"]
        cls.LeaveType = cls.env["hr.leave.type"]
        cls.LeaveAlloction = cls.env["hr.leave.allocation"]

    def create_contract(
        self, eid, state, kanban_state, start, end=None, trial_end=None
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
            }
        )

    def apply_cron(self):
        self.env.ref(
            "payroll_policy_accrual.hr_accrual_policy_cron"
        ).method_direct_trigger()

    def test_get_latest_policy(self):
        """Latest policy at given date should be returned"""

        pMarch = self.Policy.create({"name": "P1", "date": date(2020, 3, 1)})
        pDec = self.Policy.create({"name": "P1", "date": date(2020, 12, 1)})
        pJan = self.Policy.create({"name": "P1", "date": date(2020, 1, 1)})
        pg = self.PolicyGroup.create(
            {
                "name": "PGroup",
                "accr_policy_ids": [(6, 0, [pMarch.id, pDec.id, pJan.id])],
            }
        )
        ap = self.Policy.get_latest_policy(pg, date.today())

        self.assertEqual(pDec, ap)

    def test_get_latest_policy_with_future(self):
        """Latest policy must not be in the future"""

        pastDate = date.today() - relativedelta(days=5)
        futureDate = date.today() + relativedelta(days=1)
        pFuture = self.Policy.create({"name": "PF", "date": futureDate})
        pPast = self.Policy.create({"name": "PP", "date": pastDate})
        pg = self.PolicyGroup.create(
            {
                "name": "PGroup",
                "accr_policy_ids": [(6, 0, [pFuture.id, pPast.id])],
            }
        )
        ap = self.Policy.get_latest_policy(pg, date.today())

        self.assertEqual(pPast, ap)

    def test_constraint_employed_days(self):
        """Verify correctly wheter an employee falls within employed days constraint"""

        # Setup Employee past minimum days
        start = date.today() - timedelta(days=100)
        ee = self.Employee.create({"name": "John"})
        cc = self.create_contract(ee.id, "draft", "done", start)
        cc.signal_confirm()
        # Setup Employee still in minimum days
        start = date.today()
        ee2 = self.Employee.create({"name": "Paul"})
        cc2 = self.create_contract(ee2.id, "draft", "done", start)
        cc2.signal_confirm()

        # Create policy with minimum employed days = 30
        aa = self.Accrual.create({"name": "ACCR"})
        line = self.PolicyLine.create(
            {
                "name": "A",
                "code": "A",
                "accrual_id": aa.id,
                "type": "standard",
                "minimum_employed_days": 30,
            }
        )

        # past min. days
        self.assertTrue(line.pass_constraints(ee))
        # still hasn't completed min days
        self.assertFalse(line.pass_constraints(ee2))

    def test_annual_accrual(self):
        """Accrual created for employee after first month"""

        # Setup Employee
        start = date.today() - relativedelta(months=1)
        dLastRun = date.today() - relativedelta(days=4)
        dtLastRun = datetime.combine(dLastRun, datetime.min.time())
        ee = self.Employee.create({"name": "John"})
        cc = self.create_contract(ee.id, "draft", "done", start)
        cc.signal_confirm()

        # Create policy that accrues 24 days/year
        lt = self.LeaveType.create({"name": "Leave type", "code": "LT"})
        aa = self.Accrual.create({"name": "24 ANNUAL ACCR", "holiday_status_id": lt.id})
        policy = self.Policy.create(
            {
                "name": "Annual leave",
                "date": date.today(),
            }
        )
        pl = self.PolicyLine.create(
            {
                "name": "Fixed",
                "code": "FIX",
                "accrual_id": aa.id,
                "policy_id": policy.id,
                "calculation_frequency": "monthly",
                "frequency_on_hire_date": True,
                "accrual_rate": 24,
            }
        )
        pg = self.PolicyGroup.create(
            {"name": "PG", "accr_policy_ids": [(6, 0, [policy.id])]}
        )
        cc.policy_group_id = pg.id

        self.AccrualJob.create(
            {"name": dLastRun, "execution_time": dtLastRun, "policy_line_id": pl.id}
        )
        self.assertEqual(0, len(aa.line_ids))

        self.apply_cron()

        self.assertEqual(1, len(aa.line_ids))
        self.assertEqual(date.today(), aa.line_ids[0].date)
        self.assertEqual(ee, aa.line_ids[0].employee_id)
        self.assertEqual(
            0, fields.Float.compare(aa.line_ids[0].amount, 2.0, precision_digits=2)
        )
        lva = self.LeaveAlloction.search(
            [("employee_id", "=", ee.id), ("from_accrual", "=", True)]
        )
        self.assertEqual(1, len(lva))
        self.assertEqual(
            0,
            fields.Float.compare(
                aa.line_ids[0].amount, lva[0].number_of_days, precision_digits=2
            ),
        )
        job = pl.job_ids.filtered(lambda j: j.name == start + relativedelta(months=1))
        self.assertEqual(5, len(pl.job_ids))
        self.assertEqual(1, len(job.accrual_line_ids))
        self.assertEqual(1, len(job.holiday_ids))
        self.assertEqual(job.holiday_ids[0], lva[0])
        self.assertIn(job.holiday_ids[0].state, ["validate", "validate1"])
        self.assertTrue(job.execution_time)
        self.assertTrue(job.end_time)
        self.assertGreater(job.end_time, pl.job_ids[0].execution_time)
