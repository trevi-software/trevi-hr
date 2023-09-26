# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from odoo import fields
from odoo.tests import Form, common


class TestPayslipAmendment(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPayslipAmendment, cls).setUpClass()

        cls.Period = cls.env["hr.payroll.period"]
        cls.Schedule = cls.env["hr.payroll.period.schedule"]
        cls.Run = cls.env["hr.payslip.run"]
        cls.Payslip = cls.env["hr.payslip"]
        cls.Amendment = cls.env["hr.payslip.amendment"]

        cls.eeSally = cls.env["hr.employee"].create({"name": "Sally"})

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
        self,
        eid,
        state,
        kanban_state,
        start=None,
        end=None,
        trial_end=None,
        pps_id=None,
    ):
        if start is None:
            start = date.today()
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

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def test_amendment_in_period(self):

        # Create Payroll Period
        #
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

        # Create Contract
        self.create_contract(
            self.eeSally.id, "close", "normal", start.date(), end.date(), pps_id=pps.id
        )
        self.apply_contract_cron()

        # Create Payslip Amendment
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 500,
                "period_id": pp.id,
            }
        )
        psa._onchange_period_id()
        psa.do_validate()

        # Create Payslip
        slip = pp.create_payslip(self.eeSally.id, run_id=run.id)

        input_lines = slip.input_line_ids.filtered(lambda self: self.code == "SALECOM")
        self.assertEqual(
            len(input_lines), 1, "There must be ONE payslip input line for SALECOM"
        )

        _res1 = fields.Float.compare(input_lines[0].amount, 500.0, precision_digits=2)
        self.assertEqual(_res1, 0, "The Input amount should be equal to 500.00")
        self.assertEqual(
            psa.state, "done", "The payslip amendment must be in 'done' state"
        )

    def test_amendment_not_in_period(self):

        # Create Payroll Period
        #
        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        start2 = datetime(2021, 2, 1)
        end2 = datetime(2021, 2, 28, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        pp = self.create_payroll_period(pps.id, start, end)
        pp2 = self.create_payroll_period(pps.id, start2, end2)
        run = self.Run.create(
            {
                "name": "Run A",
                "date_start": start.date(),
                "date_end": end.date(),
                "period_id": pp.id,
            }
        )

        # Create Contract
        self.create_contract(
            self.eeSally.id, "close", "normal", start.date(), end.date(), pps_id=pps.id
        )
        self.apply_contract_cron()

        # Create Payslip Amendment
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 500,
                "period_id": pp2.id,
            }
        )
        psa._onchange_period_id()
        psa.do_validate()

        # Create Payslip
        slip = pp.create_payslip(self.eeSally.id, run_id=run.id)

        input_lines = slip.input_line_ids.filtered(lambda self: self.code == "SALECOM")
        self.assertEqual(
            len(input_lines), 1, "There must be ONE payslip input line for SALECOM"
        )

        _res1 = fields.Float.compare(input_lines[0].amount, 0.0, precision_digits=2)
        self.assertEqual(_res1, 0, "The paylip amendment should NOT have been applied")

    def test_amendment_in_period2(self):
        """
        The amendment should be applied even when the employee contract is
        less than payroll period.
        """

        # Create Payroll Period
        #
        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        cstart = datetime(2021, 1, 10)
        cend = datetime(2021, 1, 21, 23, 59, 59)
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

        # Create Contract
        self.create_contract(
            self.eeSally.id,
            "close",
            "normal",
            cstart.date(),
            cend.date(),
            pps_id=pps.id,
        )
        self.apply_contract_cron()

        # Create Payslip Amendment
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 500,
                "period_id": pp.id,
            }
        )
        psa._onchange_period_id()
        psa.do_validate()

        # Create Payslip
        slip = pp.create_payslip(self.eeSally.id, run_id=run.id)

        input_lines = slip.input_line_ids.filtered(lambda self: self.code == "SALECOM")
        self.assertEqual(
            len(input_lines), 1, "There must be ONE payslip input line for SALECOM"
        )

        _res1 = fields.Float.compare(input_lines[0].amount, 500.0, precision_digits=2)
        self.assertEqual(_res1, 0, "The Input amount should be equal to 500.00")
        self.assertEqual(
            psa.state, "done", "The payslip amendment must be in 'done' state"
        )

    def test_onchange_amendment(self):

        # Create Payroll Period
        #
        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 31, 23, 59, 59)
        pps = self.create_payroll_schedule("manual", start.date())
        pp = self.create_payroll_period(pps.id, start, end)

        # Create Contract
        self.create_contract(
            self.eeSally.id, "close", "normal", start.date(), end.date(), pps_id=pps.id
        )
        self.apply_contract_cron()

        # Create Payslip Amendment
        f = Form(self.Amendment)
        f.employee_id = self.eeSally
        f.input_id = self.input_commision
        f.amount = 10.00
        f.period_id = pp

        self.assertEqual(
            f.date,
            end.date(),
            "The date field is automatically set when the period is set",
        )

        f.save()
