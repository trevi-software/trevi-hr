# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2015 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from pytz import timezone, utc

from odoo import _, api, exceptions, fields, models

DEFAULT_BATCHBY = "department"


class ProcessingWizard(models.TransientModel):

    _name = "hr.payroll.processing"
    _description = "HR Payroll Processing Wizard"

    @api.model
    def _get_pp(self):

        res = False
        if self.env.context is not None:
            res = self.env.context.get("active_id", False)
        return res

    @api.model
    def _get_contracts(self):

        res = []
        Contract = self.env["hr.contract"]
        pp_id = self._get_pp()
        if pp_id:
            pp = self.env["hr.payroll.period"].browse(pp_id)
            res = Contract.search(
                [
                    ("date_start", "<=", pp.date_end),
                    ("state", "=", "draft"),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", pp.date_start),
                ]
            )
        return res

    state = fields.Selection(
        selection=[
            ("apprvcn", "Contracts"),
            ("apprvlv", "Leaves"),
            ("holidays", "Holidays"),
        ],
        default="apprvcn",
        readonly=True,
    )
    payroll_period_id = fields.Many2one(
        string="Payroll Period",
        comodel_name="hr.payroll.period",
        default=_get_pp,
        readonly=True,
    )

    # Contracts in Draft State
    contract_ids = fields.Many2many(
        string="Contracts to Approve",
        comodel_name="hr.contract",
        relation="hr_payroll_processing_contracts_rel",
        column1="wizard_id",
        column2="contract_id",
        default=_get_contracts,
        readonly=True,
    )

    # Leaves in Draft State
    leave_ids = fields.Many2many(
        string="Leaves to Approve",
        comodel_name="hr.leave",
        relation="hr_payroll_processing_leaves_rel",
        column1="wizard_id",
        column2="leave_id",
        readonly=True,
    )

    # Public Holidays
    public_holiday_ids = fields.Many2many(
        string="Public Holidays",
        comodel_name="hr.holidays.public.line",
        relation="hr_payroll_processing_hol_rel",
        readonly=True,
    )

    def _populate_leaves(self):

        self.ensure_one()
        Leaves = self.env["hr.leave"]
        res = Leaves.search(
            [
                ("date_from", "<=", self.payroll_period_id.date_end),
                ("date_to", ">=", self.payroll_period_id.date_start),
                ("state", "not in", ["cancel", "refuse", "validate"]),
            ]
        )
        self.write({"leave_ids": [(6, 0, res.ids)]})
        return

    def _populate_holidays(self):

        self.ensure_one()
        holiday_ids = []
        pp = self.payroll_period_id

        # XXX - Someone interested in DST should fix this.
        #
        local_tz = timezone(pp.schedule_id.tz)
        utcdtStart = utc.localize(pp.date_start, is_dst=False)
        dtStart = utcdtStart.astimezone(local_tz)
        utcdtEnd = utc.localize(pp.date_end, is_dst=False)
        dtEnd = utcdtEnd.astimezone(local_tz)
        holiday_ids = self.env["hr.holidays.public.line"].search(
            ["&", ("date", ">=", dtStart.date()), ("date", "<=", dtEnd.date())]
        )
        if len(holiday_ids) > 0:
            self.write({"public_holiday_ids": [(6, 0, holiday_ids.ids)]})
        else:
            self.write({"public_holiday_ids": [(5,)]})

        return

    def state_back(self):

        wizard = self
        if wizard.state == "holidays":
            self.state_leaves()
        elif wizard.state == "apprvlv":
            self.state_contracts()

        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.payroll.processing",
            "res_id": self.ids[0],
            "type": "ir.actions.act_window",
            "target": "new",
            "nodestroy": True,
            "context": self.env.context,
        }

    def state_next(self):

        wizard = self
        if wizard.state == "apprvcn":
            self.state_leaves()
        elif wizard.state == "apprvlv":
            self.state_holidays()

        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.payroll.processing",
            "res_id": self.ids[0],
            "type": "ir.actions.act_window",
            "target": "new",
            "nodestroy": True,
            "context": self.env.context,
        }

    def generate_payslips(self):

        self.create_payroll_register()
        return {"type": "ir.actions.act_window_close"}

    def state_contracts(self):

        self.write({"state": "apprvcn"})

    def state_leaves(self):

        self._populate_leaves()
        self.write({"state": "apprvlv"})

    def state_holidays(self):

        self._populate_holidays()
        self.write({"state": "holidays"})

    def create_payroll_register(self):

        self.ensure_one()
        if self.payroll_period_id.state in ["payment", "closed"]:
            raise exceptions.UserError(
                _(
                    "You cannot modify a payroll register once it has been marked for payment"
                )
            )

        if self.payroll_period_id.state not in ["open", "ended", "locked", "generate"]:
            raise exceptions.UserError(_("You must lock the payroll period first."))

        # Create the payroll register
        register_values = {
            "name": _("%s Payroll Sheet" % (self.payroll_period_id.name)),
            "date_start": self.payroll_period_id.date_start,
            "date_end": self.payroll_period_id.date_end,
            "period_id": self.payroll_period_id.id,
        }

        # Get list of departments
        department_ids = self.env["hr.department"].search([])

        register = self.create_payslip_runs(register_values, department_ids)
        register.set_denominations()

    @api.model
    def _remove_register(self, register):

        for run in register.run_ids:
            run.slip_ids.unlink()
        register.run_ids.unlink()
        register.unlink()

    def get_period_schedule_contracts(self, period):
        """Get contracts attached to payroll schedule of 'period'."""

        return period.schedule_id.contract_ids

    def _get_employees_from_department(self, dept, contracts, date_start, date_end):
        c_ids = self.env["hr.contract"].search(
            [
                ("id", "in", contracts.ids),
                ("date_start", "<=", date_end),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", date_start),
                "|",
                ("department_id.id", "=", dept.id),
                ("employee_id.department_id", "=", dept.id),
            ]
        )
        return c_ids.mapped("employee_id")

    def _create_batches(
        self,
        register,
        contracts,
        departments,
        date_start,
        date_end,
        batch_by=DEFAULT_BATCHBY,
    ):

        batches = self.env["hr.payslip.run"]
        if batch_by != DEFAULT_BATCHBY:
            return batches

        # Create payslip batch (run) for each department
        #
        for dept in departments:
            ee_ids = self._get_employees_from_department(
                dept, contracts, date_start, date_end
            )
            if len(ee_ids) == 0:
                continue

            run_res = {
                "name": dept.complete_name,
                "date_start": date_start,
                "date_end": date_end,
                "register_id": register.id,
                "period_id": register.period_id.id,
                "department_ids": [(6, 0, [dept.id])],
            }
            batch = self.env["hr.payslip.run"].create(run_res)

            # Create a pay slip for each employee in each department that has
            # a contract in the pay period schedule of this pay period
            payslips = self.env["hr.payslip"]
            ee_ids = ee_ids.sorted(key=lambda e: e.name)
            for ee in ee_ids:
                if not self.payroll_period_id.process_employee(ee.id):
                    continue

                payslips |= self.payroll_period_id.create_payslip(ee.id, batch.id)

            # Calculate payroll for all the pay slips in this batch (run)
            payslips.compute_sheet()
            batches |= batch

        return batches

    def create_payslip_runs(self, register_values, dept_ids):
        """
        Create payslips for employees, in all departments, that have a contract in
        this pay period's schedule.
        """

        # DateTime in db is stored as naive UTC. Convert it to explicit UTC and then convert
        # that into the time zone of the pay period schedule.
        #
        period = self.payroll_period_id
        local_tz = timezone(period.schedule_id.tz)
        utcdt_start = utc.localize(period.date_start)
        tzdt_start = utcdt_start.astimezone(local_tz)
        utcdt_end = utc.localize(period.date_end)
        tzdt_end = utcdt_end.astimezone(local_tz)

        date_start = tzdt_start.date()
        date_end = tzdt_end.date()
        previous_register = period.register_id
        contract_ids = self.get_period_schedule_contracts(period)
        batch_by = self.get_batch_criteria()

        # Remove any pre-existing payroll registers
        if previous_register:
            self._remove_register(previous_register)

        # Create Payroll Register
        register = self.env["hr.payroll.register"].create(register_values)

        # Create payslip batches
        self._create_batches(
            register, contract_ids, dept_ids, date_start, date_end, batch_by
        )

        # Attach payroll register to this pay period
        period.register_id = register

        return register

    def get_batch_criteria(self):
        return DEFAULT_BATCHBY
