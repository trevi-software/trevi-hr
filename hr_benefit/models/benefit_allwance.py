# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError

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
    _sql_constraints = [
        (
            "unique_date_benefit_id",
            "UNIQUE(effective_date,benefit_id)",
            _("Effective date must be unique per advantage in a benefit!"),
        )
    ]

    benefit_id = fields.Many2one(string="Benefit", comodel_name="hr.benefit")
    effective_date = fields.Date(required=True)
    min_employed_days = fields.Integer(
        string="Minimum Employed Days",
        help="Number of days of employment before employee is eligible for this advantage.",
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

    def name_get(self):
        res = []
        for rec in self:
            res.append(
                (rec.id, "{} {}".format(rec.benefit_id.name, rec.effective_date))
            )
        return res

    def get_claims_in_period(self, employee_id, day):

        d = day
        period = self.reim_limit_period
        if period == "monthly":
            diff = d.day - int(self.reim_period_month_day)
            if diff == 0:
                dStart = d
            elif diff > 0:
                dStart = d + timedelta(days=-(diff))
            else:
                dStart = d + relativedelta(months=-1, days=diff)
            dNextStart = dStart + relativedelta(months=+1)
        elif period == "annual":
            day_diff = d.day - int(self.reim_period_annual_day)
            month_diff = d.month - int(self.reim_period_annual_month)
            if month_diff == 0:
                dStart = d
            elif month_diff > 0:
                dStart = d + relativedelta(months=-(month_diff))
            else:
                # month_diff is negative, but: -(-) = +
                dStart = d + relativedelta(months=-(month_diff))
            if day_diff > 0:
                dStart = dStart + timedelta(days=-(day_diff))
            elif day_diff < 0:
                dStart = dStart + relativedelta(months=-1, days=day_diff)
            dNextStart = dStart + relativedelta(years=+1)
        else:
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
                "SELECT SUM(amount_approved) FROM hr_benefit_claim " "WHERE id in %s",
                (tuple(claim_ids.ids),),
            )
            res = self.env.cr.fetchall()[0][0]
        return res

    def get_reimburse_remaining(self, employee_id, day):

        self.ensure_one()
        if self.type != "reimburse":
            raise UserError(
                _(
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
        if len(policies) == 0:
            res = 0.0
        elif self.reim_nolimit:
            res = 0.0
        elif self.reim_limit_period:
            claims = self.get_claims_in_period(employee_id, day)
            unclaimed = self.reim_limit_amount - claims
            res = (unclaimed < 0.01) and 0.00 or unclaimed
        return res
