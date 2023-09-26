# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from pytz import timezone, utc

from odoo import _, api, exceptions, fields, models
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT,
)


class HrPayslipRun(models.Model):

    _inherit = "hr.payslip.run"

    period_id = fields.Many2one("hr.payroll.period", "Payroll Period")

    @api.model
    def _get_confirmed_amendments(self, period_id):

        psa_ids = self.env["hr.payslip.amendment"].search(
            [
                ("pay_period_id", "=", period_id),
                ("state", "in", ["validate"]),
            ]
        )
        return psa_ids

    def recalculate(self):

        Payslip = self.env["hr.payslip"]
        PayrollPeriod = self.env["hr.payroll.period"]

        run = self.browse(self.ids[0])
        register_id = run.register_id.id
        period_id = run.register_id.period_id.id
        dept_ids = [d.id for d in run.department_ids]

        # Get relevant data from the period object
        p_data = PayrollPeriod.browse(period_id).read(
            ["name", "date_start", "date_end", "schedule_id", "register_id", "state"],
        )

        if p_data["state"] not in ["open", "ended", "locked", "generate"]:
            raise exceptions.UserError(
                _("Invalid Action")
                + "\n"
                + _("You must lock the payroll period first.")
            )

        s_data = (
            self.env["hr.payroll.period.schedule"]
            .browse(p_data["schedule_id"][0])
            .read(["annual_pay_periods", "contract_ids", "tz"])
        )

        # DateTime in db is stored as naive UTC. Convert it to explicit UTC and then convert
        # that into the time zone of the pay period schedule.
        #
        local_tz = timezone(s_data["tz"])
        utcDTStart = utc.localize(datetime.strptime(p_data["date_start"], OE_DTFORMAT))
        loclDTStart = utcDTStart.astimezone(local_tz)
        utcDTEnd = utc.localize(datetime.strptime(p_data["date_end"], OE_DTFORMAT))
        loclDTEnd = utcDTEnd.astimezone(local_tz)

        # Create payslips for employees, in all departments, that have a contract in this
        # pay period's schedule
        # Remove any pre-existing payroll registers
        for run in self:
            run_data = run.read(["slip_ids"])
            Payslip.browse(run_data["slip_ids"]).unlink()
            self.create_payslip_runs(
                period_id,
                run.id,
                register_id,
                dept_ids,
                s_data["contract_ids"],
                loclDTStart.date(),
                loclDTEnd.date(),
                s_data["annual_pay_periods"],
            )

        return True

    @api.model
    def create_payslip_runs(
        self,
        period_id,
        run_id,
        register_id,
        dept_ids,
        contract_ids,
        date_start,
        date_end,
        annual_pay_periods,
    ):

        Contract = self.env["hr.contract"]
        Department = self.env["hr.department"]
        Employee = self.env["hr.employee"]
        PayslipRun = self.env["hr.payslip.run"]
        PayrollPeriod = self.env["hr.payroll.period"]

        # Get Pay Slip Amendments, Employee ID, and the amount of the amendment
        #
        psa_codes = []
        psa_ids = self._get_confirmed_amendments(period_id)
        for psa in self.env["hr.payslip.amendment"].browse(psa_ids):
            psa_codes.append((psa.employee_id.id, psa.input_id.code, psa.amount))

        # Keep track of employees that have already been included
        seen_ee_ids = []

        # Create payslip batch (run) for each department
        #
        for dept in Department.browse(dept_ids):
            ee_ids = []
            c_ids = Contract.search(
                [
                    ("id", "in", contract_ids),
                    ("date_start", "<=", date_end.strftime(OE_DFORMAT)),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", date_start.strftime(OE_DFORMAT)),
                    "|",
                    ("department_id.id", "=", dept.id),
                    ("employee_id.department_id.id", "=", dept.id),
                ]
            )
            c2_ids = Contract.search(
                [
                    ("id", "in", contract_ids),
                    ("date_start", "<=", date_end.strftime(OE_DFORMAT)),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", date_start.strftime(OE_DFORMAT)),
                    ("employee_id.status", "in", ["pending_inactive", "inactive"]),
                    "|",
                    ("job_id.department_id.id", "=", dept.id),
                    ("end_job_id.department_id.id", "=", dept.id),
                ]
            )
            for i in c2_ids:
                if i not in c_ids:
                    c_ids.append(i)

            c_data = c_ids.read(["employee_id"])
            for data in c_data:
                if data["employee_id"][0] not in ee_ids:
                    ee_ids.append(data["employee_id"][0])

            if len(ee_ids) == 0:
                continue

            # Alphabetize
            ee_ids = Employee.search(
                [
                    ("id", "in", ee_ids),
                    "|",
                    ("active", "=", False),
                    ("active", "=", True),
                ],
            )

            period = PayrollPeriod.browse(period_id)
            run_res = {
                "name": dept.complete_name,
                "date_start": date_start,
                "date_end": date_end,
                "register_id": register_id,
                "journal_id": period.journal_id.id,
            }
            PayslipRun.browse(run_id).write(run_res)

            # Create a pay slip for each employee in each department that has
            # a contract in the pay period schedule of this pay period
            #
            slip_ids = []
            for ee in ee_ids:

                if ee.id in seen_ee_ids:
                    continue

                # _logger.warning('Employee: %s', ee.name)
                slip_id = PayrollPeriod.create_payslip(
                    ee.id, date_start, date_end, psa_codes, run_id, annual_pay_periods
                )
                if slip_id is not False:
                    slip_ids.append(slip_id)

                seen_ee_ids.append(ee.id)

            # Calculate payroll for all the pay slips in this batch (run)
            slip_ids.compute_sheet()

        return
