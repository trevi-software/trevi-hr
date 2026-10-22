# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import calendar
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

DAY_SELECT = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
    ("9", "9"),
    ("10", "10"),
    ("11", "11"),
    ("12", "12"),
    ("13", "13"),
    ("14", "14"),
    ("15", "15"),
    ("16", "16"),
    ("17", "17"),
    ("18", "18"),
    ("19", "19"),
    ("20", "20"),
    ("21", "21"),
    ("22", "22"),
    ("23", "23"),
    ("24", "24"),
    ("25", "25"),
    ("26", "26"),
    ("27", "27"),
    ("28", "28"),
    ("29", "29"),
    ("30", "30"),
    ("31", "31"),
]


class BenefitAdvantage(models.Model):
    _name = "hr.benefit.advantage"
    _description = "Employee Benefit Policy Earning Line"
    _rec_name = "effective_date"
    _order = "benefit_id,effective_date desc"
    _unique_date_benefit_id = models.Constraint(
        "UNIQUE(effective_date,benefit_id)",
        "Effective date must be unique per advantage in a benefit!",
    )

    benefit_id = fields.Many2one(comodel_name="hr.benefit")
    effective_date = fields.Date(required=True)
    min_employed_days = fields.Integer(
        string="Minimum Employed Days",
        help="Number of days of employment before "
        "employee is eligible for this advantage.",
    )
    type = fields.Selection(
        string="Earning Type",
        selection=[
            ("allowance", "Allowance"),
            ("reimburse", "Expense Reimbursement"),
            ("loan", "Loan"),
        ],
        required=True,
    )
    allowance_amount = fields.Float(
        string="Default Amount",
        digits="Account",
        help="If the allowance is not calculated in the salary "
        "rule this is the amount of the allowance",
    )
    reim_nolimit = fields.Boolean(string="No Limit")
    reim_limit_amount = fields.Float(string="Limit Amount", digits="Account")
    reim_limit_period = fields.Selection(
        string="Limit Period",
        selection=[
            ("monthly", "Monthly"),
            ("annual", "Annual"),
        ],
    )
    reim_period_month_day = fields.Selection(
        string="First Day of Cycle",
        selection=DAY_SELECT,
    )
    reim_period_annual_month = fields.Selection(
        string="Month",
        selection=[
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "April"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
    )
    reim_period_annual_day = fields.Selection(
        string="Day of Month",
        selection=DAY_SELECT,
    )
    loan_amount = fields.Float(
        digits="Payroll", help="The amount advanced to the employee"
    )
    category_ids = fields.Many2many(
        string="Employee Categories",
        comodel_name="hr.employee.category",
        relation="benefit_advantage_category_rel",
        column1="advantage_id",
        column2="category_id",
    )
    job_ids = fields.Many2many(
        string="Included Job Positions",
        comodel_name="hr.job",
        relation="benefit_advantage_job_rel",
        column1="advantage_id",
        column2="job_id",
        help="Applies only to these job positions",
    )
    invert_categories = fields.Boolean(
        string="Exclude Categories",
        help="If this is checked invert the sense of the "
        "match for the categories list. Exclude employees "
        "in the selected categories.",
    )
    invert_jobs = fields.Boolean(
        string="Exclude Jobs",
        help="If this is checked invert the sense of the "
        "match for the jobs list. Exclude employees in "
        "the selected jobs.",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="benefit_id.company_id",
        store=True,
        index=True,
    )

    @api.depends("benefit_id", "effective_date")
    def _compute_display_name(self):
        # ``name_get`` was removed in Odoo 19; the display name is computed
        # explicitly instead.
        for rec in self:
            rec.display_name = f"{rec.benefit_id.name} {rec.effective_date}"

    @api.constrains(
        "type",
        "reim_limit_period",
        "reim_period_month_day",
        "reim_period_annual_month",
        "reim_period_annual_day",
    )
    def _check_reimbursement_settings(self):
        # ``exists()`` skips records that a concurrent or stale write refers to
        # but that are no longer in the database.
        for rec in self.exists():
            if rec.type != "reimburse":
                continue
            if rec.reim_limit_period == "monthly" and not rec.reim_period_month_day:
                raise ValidationError(
                    self.env._(
                        "A monthly reimbursement limit requires the "
                        "'First Day of Cycle'."
                    )
                )
            if rec.reim_limit_period == "annual" and not (
                rec.reim_period_annual_month and rec.reim_period_annual_day
            ):
                raise ValidationError(
                    self.env._(
                        "An annual reimbursement limit requires both the "
                        "cycle start month and day."
                    )
                )

    @staticmethod
    def _clamp_day(year, month, day):
        """Return ``date(year, month, day)`` clamped to the month's last day."""
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(day, last_day))

    def _cycle_start(self, day):
        """Return the (start, next start) boundaries of the cycle containing ``day``."""
        if self.reim_limit_period == "monthly":
            start_day = int(self.reim_period_month_day)
            start = self._clamp_day(day.year, day.month, start_day)
            if start > day:
                previous = day - relativedelta(months=1)
                start = self._clamp_day(previous.year, previous.month, start_day)
            end = start + relativedelta(months=1)
        elif self.reim_limit_period == "annual":
            month = int(self.reim_period_annual_month)
            start_day = int(self.reim_period_annual_day)
            start = self._clamp_day(day.year, month, start_day)
            if start > day:
                start = self._clamp_day(day.year - 1, month, start_day)
            end = self._clamp_day(start.year + 1, month, start_day)
        else:
            return None, None
        return start, end

    def get_claims_in_period(self, employee_id, day):
        dStart, dNextStart = self._cycle_start(day)
        if dStart is None:
            return 0.00

        claim_obj = self.env["hr.benefit.claim"]
        claim_ids = claim_obj.search(
            [
                ("employee_id", "=", employee_id.id),
                ("benefit_policy_id.benefit_id", "=", self.benefit_id.id),
                ("benefit_policy_id.start_date", "<", dNextStart),
                "|",
                ("benefit_policy_id.end_date", "=", False),
                ("benefit_policy_id.end_date", ">=", dStart),
                ("date", ">=", dStart),
                ("date", "<", dNextStart),
                ("state", "=", "approve"),
            ]
        )
        res = 0.00
        if len(claim_ids) > 0:
            self.env.cr.execute(
                "SELECT SUM(amount_approved) FROM hr_benefit_claim WHERE id in %s",
                (tuple(claim_ids.ids),),
            )
            res = self.env.cr.fetchall()[0][0]
        return res

    def get_reimburse_remaining(self, employee_id, day):
        self.ensure_one()
        if self.type != "reimburse":
            raise UserError(
                self.env._(
                    "Wrong earning type for this operation. "
                    "Use 'Expense Re-imbursement' instead."
                )
            )
        policies = self.env["hr.benefit.policy"].search(
            [
                ("benefit_id", "=", self.benefit_id.id),
                ("employee_id", "=", employee_id.id),
                "|",
                ("end_date", "=", False),
                ("end_date", ">=", day),
            ]
        )
        if len(policies) == 0 or self.reim_nolimit:
            return 0.0
        if not self.reim_limit_period:
            raise UserError(
                self.env._(
                    "The reimbursement earning line has no limit period configured."
                )
            )
        claims = self.get_claims_in_period(employee_id, day)
        unclaimed = self.reim_limit_amount - claims
        return unclaimed if unclaimed >= 0.01 else 0.00
