# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import _, api, exceptions, fields, models

from .hr_payroll_period_schedule import get_period_year


class HrPayrollPeriod(models.Model):

    _name = "hr.payroll.period"
    _description = "Payroll Periods"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start, name desc"

    name = fields.Char(string="Description", required=True)
    period_name = fields.Char()
    schedule_id = fields.Many2one(
        string="Payroll Period Schedule",
        comodel_name="hr.payroll.period.schedule",
        required=True,
        check_company=True,
    )
    date_start = fields.Datetime(string="Start Date", required=True)
    date_end = fields.Datetime(string="End Date", required=True)
    state = fields.Selection(
        selection=[
            ("open", "Open"),
            ("ended", "End of Period Processing"),
            ("generate", "Generating Payslips"),
            ("payment", "Payment"),
            ("closed", "Closed"),
        ],
        default="open",
        index=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    run_ids = fields.One2many(
        comodel_name="hr.payslip.run",
        inverse_name="period_id",
        string="Payslip Batches",
    )
    exception_ids = fields.Many2many(
        string="Pay Slip Exceptions",
        comodel_name="hr.payslip.exception",
        compute="_compute_pex_all",
    )

    def _get_pex(self, severity):

        self.ensure_one()
        PayslipException = self.env["hr.payslip.exception"]

        slip_ids = []
        for run in self.run_ids:
            [slip_ids.append(slip.id) for slip in run.slip_ids]
        ex = PayslipException.search(
            [("severity", "=", severity), ("slip_id", "in", slip_ids)]
        )
        return ex.ids

    @api.depends("run_ids.slip_ids")
    def _compute_pex_all(self):

        for period in self:
            res = period._get_pex("critical")
            res += period._get_pex("medium")
            res += period._get_pex(
                "low",
            )
            period.exception_ids = [(6, 0, res)]

    def _track_subtype(self, init_values):
        self.ensure_one()
        if "state" in init_values:
            if self.state == "open":
                return self.env.ref("payroll_periods.mt_state_open")
            elif self.state == "end":
                return self.env.ref("payroll_periods.mt_state_end")
            elif self.state == "lock":
                return self.env.ref("payroll_periods.mt_state_lock")
            elif self.state == "generate":
                return self.env.ref("payroll_periods.mt_state_generate")
            elif self.state == "payment":
                return self.env.ref("payroll_periods.mt_state_payment")
            elif self.state == "close":
                return self.env.ref("payroll_periods.mt_state_close")
        return super(HrPayrollPeriod, self)._track_subtype(init_values)

    @api.model
    def is_ended(self):

        #
        # XXX - Someone who cares about DST should update this code to handle it.
        #

        self.ensure_one()
        utc_tz = timezone("UTC")
        utcDtNow = utc_tz.localize(datetime.now(), is_dst=False)
        dtEnd = self.date_end
        utcDtEnd = utc_tz.localize(dtEnd, is_dst=False)
        if utcDtNow > utcDtEnd + timedelta(
            minutes=(self.schedule_id.ot_max_rollover_hours * 60)
        ):
            return True
        return False

    @api.model
    def try_signal_end_period(self):
        """Method called, usually by cron, to transition any payroll periods
        that are past their end date.
        """

        #
        # XXX - Someone who cares about DST should update this code to handle it.
        #

        utc_tz = timezone("UTC")
        utcDtNow = utc_tz.localize(datetime.now(), is_dst=False)
        period_ids = self.search(
            [
                ("state", "in", ["open"]),
                ("date_end", "<=", utcDtNow.strftime("%Y-%m-%d %H:%M:%S")),
            ]
        )
        period_ids.set_state_ended()

    @api.model
    def get_utc_times(self, period):

        #
        # XXX - Someone who cares about DST should update this code to handle it.
        #

        utc_tz = timezone("UTC")
        utcDtStart = utc_tz.localize(period.date_start, is_dst=False)
        utcDtEnd = utc_tz.localize(period.date_end, is_dst=False)

        return (utcDtStart, utcDtEnd)

    def set_state_ended(self):

        self.write({"state": "ended"})

    def set_state_payment(self):

        for period in self:
            for ex in period.exception_ids:
                if ex.severity == "critical" and not ex.ignore:
                    raise exceptions.ValidationError(
                        _("Validation Error")
                        + "\n"
                        + _(
                            "Critical exceptions remain in %s. If you wish to \
                            proceed you must resolve or ignore them."
                        )
                        % (period.name)
                    )
        self.write({"state": "payment"})

    def set_state_generate(self):

        self.write({"state": "generate"})

    def set_state_closed(self):

        # When we close a pay period, also de-activate related attendances
        Attendance = self.env["hr.attendance"]

        for period in self:
            #
            # XXX - Someone who cares about DST should update this code to handle it.
            #
            utc_tz = timezone("UTC")
            utcDtStart = utc_tz.localize(period.date_start, is_dst=False)
            dt = period.date_end + relativedelta(
                hours=period.sched_id.ot_max_rollover_hours
            )
            utcDtEnd = utc_tz.localize(dt, is_dst=False)
            dtStart = utcDtStart.replace(tzinfo=None)
            dtEnd = utcDtEnd.replace(tzinfo=None)
            for contract in period.schedule_id.contract_ids:
                employee = contract.employee_id

                # De-activate sign-in and sign-out attendance records
                punch_ids = Attendance.search(
                    [
                        ("employee_id", "=", employee.id),
                        "&",
                        ("checkin", ">=", dtStart),
                        ("check_out", "<=", dtEnd),
                    ],
                )
                punch_ids.write({"active": False})

        return self.write({"state": "closed"})

    @api.model
    def get_contracts_hook(self, ee, dPeriodStart, dPeriodEnd):
        found_contracts = []
        dEarliestContractStart = False
        dLastContractEnd = False
        open_contract = False
        for contract in ee.contract_ids:

            # Does employee have a contract in this pay period?
            #
            dContractStart = contract.date_start
            dContractEnd = False
            if contract.date_end:
                dContractEnd = contract.date_end
            if dContractStart > dPeriodEnd or (
                dContractEnd and dContractEnd < dPeriodStart
            ):
                continue
            else:
                found_contracts.append(contract)
                if (
                    not dEarliestContractStart
                    or dContractStart < dEarliestContractStart
                ):
                    dEarliestContractStart = dContractStart
                if not dContractEnd:
                    dLastContractEnd = False
                    open_contract = True
                elif (
                    not open_contract
                    and dContractEnd
                    and (not dLastContractEnd or dContractEnd > dLastContractEnd)
                ):
                    dLastContractEnd = dContractEnd
        return (dEarliestContractStart, dLastContractEnd, found_contracts)

    @api.model
    def payslip_create_hook(self, dictCreate):
        return dictCreate

    def create_payslip(self, employee_id, run_id=False):

        self.ensure_one()
        local_tz = timezone(self.schedule_id.tz)
        utc_pstart, utc_pend = self.get_utc_times(self)
        tz_pstart = utc_pstart.astimezone(local_tz)
        tz_pend = utc_pend.astimezone(local_tz)
        annual_pay_periods = self.schedule_id.annual_pay_periods
        dPeriodStart = tz_pstart.date()
        dPeriodEnd = tz_pend.date()
        Payslip = self.env["hr.payslip"]
        ee = self.env["hr.employee"].browse(employee_id)
        (
            dEarliestContractStart,
            dLastContractEnd,
            found_contracts,
        ) = self.get_contracts_hook(ee, dPeriodStart, dPeriodEnd)

        if len(found_contracts) == 0:
            return False

        # If the contract doesn't cover the full pay period use the contract
        # dates as start/end dates instead of the full period.
        #
        period_start_date = dPeriodStart
        period_end_date = dPeriodEnd
        temp_date_start = period_start_date
        temp_date_end = period_end_date
        if dEarliestContractStart > period_start_date:
            temp_date_start = dEarliestContractStart
        if dLastContractEnd and dLastContractEnd < period_end_date:
            temp_date_end = dLastContractEnd

        # If termination procedures have begun within the contract period, use the
        # effective date of the termination as the end date.
        #
        Termination = self.env["hr.employee.termination"]
        term_ids = Termination.search(
            [
                ("employee_id", "=", found_contracts[0].employee_id.id),
                ("employee_id.status", "in", ["pending_inactive", "inactive"]),
                ("state", "in", ["draft", "done"]),
            ]
        )
        if len(term_ids) > 0:
            for term in term_ids:
                if term.name >= temp_date_start and term.name < temp_date_end:
                    temp_date_end = term.name

        month_name, month_no, year_no = get_period_year(
            dPeriodStart, annual_pay_periods
        )
        slip_name = _("Pay Slip for %s for %s/%s") % (ee.name, year_no, month_name)
        res = {
            "employee_id": ee.id,
            "name": slip_name,
            "payslip_run_id": run_id,
            "date_from": temp_date_start,
            "date_to": temp_date_end,
        }
        # allow other modules to modify payslip creation values dict
        res = self.payslip_create_hook(res)

        slip = Payslip.create(res)
        slip.onchange_employee()
        return slip

    def print_contribution_registers(self):

        data = (
            self.env["hr.payroll.period"]
            .browse(self.ids[0])
            .read(["date_start", "date_end"])
        )
        register_ids = self.env["hr.contribution.register"].search([]).ids

        form = {"date_from": data["date_start"], "date_to": data["date_end"]}

        return {
            "type": "ir.actions.report.xml",
            "report_name": "contribution.register.lines",
            "datas": {
                "ids": register_ids,
                "form": form,
                "model": "hr.contribution.register",
            },
        }

    def rerun_payslip(self, slip):

        self.ensure_one()
        run = slip.payslip_run_id
        ee = slip.employee_id

        if self.state in ["payment", "closed"]:
            raise exceptions.UserError(
                _(
                    "Invalid Action"
                    "You cannot modify a pay slip once the period it is in has been "
                    "marked for payment."
                )
            )

        # Remove any pre-existing pay slip
        slip.unlink()
        slip = None

        # Create a pay slip
        slip = self.create_payslip(ee.id, run.id)

        # Calculate payroll for all the pay slips in this batch (run)
        slip.compute_sheet()

        return slip

    def process_employee(self, employee_id):
        """Hook method to allow subclasses to override creation of a payslip
        for an employee."""

        return True
