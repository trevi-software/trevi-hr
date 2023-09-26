# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from pytz import timezone, utc

from odoo.tests import common, new_test_user


class TestPayrollProcessing(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Employee = cls.env["hr.employee"]
        cls.Department = cls.env["hr.department"]
        cls.Period = cls.env["hr.payroll.period"]
        cls.Schedule = cls.env["hr.payroll.period.schedule"]
        cls.ContractType = cls.env["hr.contract.type"]
        cls.Users = cls.env["res.users"]
        cls.Job = cls.env["hr.job"]
        cls.Wizard = cls.env["hr.payroll.processing"]

        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="hel",
            groups="base.group_user,payroll.group_payroll_user",
            name="Payroll manager",
            email="ric@example.com",
        )

        # Contract types
        cls.ctype_fulltime = cls.ContractType.create({"name": "Full-time"})
        cls.ctype_parttime = cls.ContractType.create({"name": "Part-time"})

        # Departments
        cls.dept_rd = cls.Department.create(
            {
                "name": "Research and devlopment",
            }
        )
        cls.dept_sales = cls.Department.create(
            {
                "name": "Sales",
            }
        )
        cls.job_ux_designer = cls.Job.create(
            {
                "name": "#UX Designer",
                "department_id": cls.dept_rd.id,
            }
        )
        cls.job_sales_associate = cls.Job.create(
            {
                "name": "Sales Associate",
                "department_id": cls.dept_sales.id,
            }
        )

        # Employee
        #
        cls.emp_sally = cls.Employee.create(
            {
                "name": "Sally",
                "department_id": cls.dept_rd.id,
            }
        )
        cls.emp_john = cls.Employee.create(
            {
                "name": "John",
                "department_id": cls.dept_sales.id,
            }
        )

        cls.pay_struct = cls.env.ref("payroll.structure_base")

    def create_payroll_schedule(self, stype=False, initial_date=False):
        return self.Schedule.create(
            {
                "name": "PPS",
                "tz": "Africa/Addis_Ababa",
                "type": stype,
                "initial_period_date": initial_date,
                "batch_by_contract_type": True,
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
        contract_type_id=False,
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
                "contract_type_id": contract_type_id,
            }
        )

    def setUpCommon(self):

        # Payroll Period
        #
        start = datetime(2021, 9, 1)
        end = datetime(2021, 9, 30, 23, 59, 59)
        self.period_schedule = self.create_payroll_schedule("manual", start.date())
        self.period = self.create_payroll_period(self.period_schedule.id, start, end)
        self.period.set_state_ended()

    def test_payslip_batch_by_contract_type(self):

        self.setUpCommon()
        start = datetime(2021, 9, 1)

        # Create contracts for Sally and John
        self.create_contract(
            self.emp_sally.id,
            "draft",
            "done",
            start.date(),
            pps_id=self.period_schedule.id,
            job_id=self.job_ux_designer.id,
            contract_type_id=self.ctype_fulltime.id,
        ).signal_confirm()
        self.create_contract(
            self.emp_john.id,
            "draft",
            "done",
            start.date(),
            pps_id=self.period_schedule.id,
            job_id=self.job_sales_associate.id,
            contract_type_id=self.ctype_parttime.id,
        ).signal_confirm()

        # Start payroll wizard
        wiz = (
            self.Wizard.with_user(self.userPM)
            .with_context({"active_id": self.period.id})
            .create({})
        )

        self.assertTrue(
            wiz.batch_by_contract_type, "The wizard inherited the schedule's setting"
        )

        # Create the payroll register
        wiz.create_payroll_register()
        fulltime_batch = parttime_batch = False
        for b in self.period.register_id.run_ids:
            if "Full-time" in b.name:
                fulltime_batch = b
            elif "Part-time" in b.name:
                parttime_batch = b

        self.assertEqual(
            len(self.period.register_id.run_ids),
            2,
            "Two contract types created two payslip batches",
        )
        self.assertTrue(
            all([fulltime_batch, parttime_batch]),
            "Found both full-time and part-time batches",
        )
        self.assertTrue(fulltime_batch.slip_ids, "Full-time batch contains payslips")
        self.assertTrue(parttime_batch.slip_ids, "Part-time batch contains payslips")
        self.assertEqual(
            fulltime_batch.slip_ids[0].employee_id,
            self.emp_sally,
            "Sally is in the full-time batch run",
        )
        self.assertEqual(
            parttime_batch.slip_ids[0].employee_id,
            self.emp_john,
            "John is in the part-time batch run",
        )

    def test_wizard_uncheck_batch_by_contract_type(self):

        self.setUpCommon()
        start = datetime(2021, 9, 1)

        # Create contracts for Sally and John
        self.create_contract(
            self.emp_sally.id,
            "draft",
            "done",
            start.date(),
            pps_id=self.period_schedule.id,
            job_id=self.job_ux_designer.id,
            contract_type_id=self.ctype_fulltime.id,
        ).signal_confirm()
        self.create_contract(
            self.emp_john.id,
            "draft",
            "done",
            start.date(),
            pps_id=self.period_schedule.id,
            job_id=self.job_sales_associate.id,
            contract_type_id=self.ctype_parttime.id,
        ).signal_confirm()

        # Start payroll wizard
        wiz = (
            self.Wizard.with_user(self.userPM)
            .with_context({"active_id": self.period.id})
            .create({})
        )

        self.assertTrue(
            wiz.batch_by_contract_type, "The wizard inherited the schedule's setting"
        )

        # Create the payroll register
        wiz.batch_by_contract_type = False
        wiz.create_payroll_register()
        rd_batch = sales_batch = False
        for b in self.period.register_id.run_ids:
            if "Research" in b.name:
                rd_batch = b
            elif "Sales" in b.name:
                sales_batch = b

        self.assertEqual(
            len(self.period.register_id.run_ids),
            2,
            "Two departments created two payslip batches",
        )
        self.assertTrue(all([rd_batch, sales_batch]), "Found both departments' batches")
        self.assertTrue(rd_batch.slip_ids, "R&D batch contains payslips")
        self.assertTrue(sales_batch.slip_ids, "Sales batch contains payslips")
        self.assertEqual(
            rd_batch.slip_ids[0].employee_id,
            self.emp_sally,
            "Sally is in the R&D batch run",
        )
        self.assertEqual(
            sales_batch.slip_ids[0].employee_id,
            self.emp_john,
            "John is in the Sales batch run",
        )
