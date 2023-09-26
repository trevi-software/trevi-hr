# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import math
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BenefitPolicy(models.Model):

    _name = "hr.benefit.policy"
    _description = "Benefit Enrollment"
    _check_company_auto = True

    name = fields.Char(string="Reference", readonly=True)
    benefit_id = fields.Many2one(
        string="Benefit",
        comodel_name="hr.benefit",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    benefit_code = fields.Char(readonly=True, related="benefit_id.code", store=True)
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    start_date = fields.Date(
        string="Date of Enrollment",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    end_date = fields.Date(string="Termination Date")
    active = fields.Boolean(default=True)
    advantage_override = fields.Boolean(
        string="Change Advantage Amount",
        help="Check this field if the amount of the advantage should be changed in the policy.",
    )
    premium_override = fields.Boolean(
        string="Change Premium Amount",
        help="Check this field if the amount of the premium should be changed in the policy.",
    )
    advantage_override_amount = fields.Float(digits="Account")
    premium_override_amount = fields.Float(digits="Account")
    premium_override_total = fields.Float(digits="Account")
    advantage_amount = fields.Float(
        digits="Account",
        compute="_compute_amounts",
        inverse="_inverse_amounts",
        store=True,
    )
    premium_amount = fields.Float(
        digits="Account",
        compute="_compute_amounts",
        inverse="_inverse_amounts",
        store=True,
    )
    premium_total = fields.Float(
        digits="Account",
        compute="_compute_amounts",
        inverse="_inverse_amounts",
        store=True,
    )
    premium_installments = fields.Integer(
        string="No. of Installments",
        compute="_compute_premium_installments",
        store=True,
    )
    note = fields.Text(string="Remarks")
    state = fields.Selection(
        selection=[("draft", "Draft"), ("open", "Open"), ("done", "Done")],
        readonly=True,
        default="draft",
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, "{} {}".format(rec.name, rec.benefit_id.name)))
        return res

    @api.depends(
        "benefit_id",
        "advantage_override",
        "premium_override",
        "advantage_override_amount",
        "premium_override_amount",
        "premium_override_total",
    )
    def _compute_amounts(self):

        for rec in self:
            res = {
                "advantage_amount": 0,
                "premium_amount": 0,
                "premium_total": 0,
            }

            if not rec.benefit_id or not rec.start_date:
                rec.write(res)
                continue

            dToday = date.today()
            if rec.advantage_override:
                res["advantage_amount"] = rec.advantage_override_amount
            else:
                adv = rec.benefit_id.get_latest_advantage(dToday)
                if adv is not None:
                    if adv.type == "allowance":
                        res["advantage_amount"] = adv.allowance_amount
            if rec.premium_override:
                res["premium_amount"] = rec.premium_override_amount
                res["premium_total"] = rec.premium_override_total
            else:
                prm = rec.benefit_id.get_latest_premium(dToday)
                if prm is not None:
                    res["premium_amount"] = prm.amount
                    res["premium_total"] = prm.total_amount

            rec.write(res)

    def _inverse_amounts(self):
        for rec in self:
            if rec.advantage_override:
                rec.advantage_override_amount = rec.advantage_amount
            if rec.premium_override:
                rec.premium_override_amount = rec.premium_amount
                rec.premium_override_total = rec.premium_total

    @api.depends("start_date", "premium_amount", "premium_total")
    def _compute_premium_installments(self):

        for rec in self:
            res = {"end_date": False, "premium_installments": 0}
            if rec.premium_amount == 0:
                rec.write(res)
                return

            installments = int(
                math.ceil(float(rec.premium_total) / float(rec.premium_amount))
            )
            if installments > 0:
                dEnd = rec.start_date + relativedelta(months=+installments)
                res["end_date"] = dEnd
            res["premium_installments"] = installments
            rec.write(res)

    @api.model
    def _fail_eligibility(self, benefit_id, employee_id):

        res = False
        benefit = self.env["hr.benefit"].browse(benefit_id)

        # Check if employee has worked more than minimum number of days for benefit
        #
        if benefit.min_employed_days > 0:
            ee = self.env["hr.employee"].browse(employee_id)
            dToday = datetime.today().date()
            dHire = ee.first_contract_date
            srvc_months = ee.get_months_service_to_date(dToday=dToday)
            srvc_months = int(srvc_months)

            employed_days = 0
            dCount = dHire
            while dCount < dToday:
                employed_days += 1
                dCount += timedelta(days=+1)
            if benefit.min_employed_days > employed_days:
                res = True

        return res

    @api.model
    def create(self, vals):

        # Check if the employee is already enrolled
        #
        benefit = self.env["hr.benefit"].browse(vals["benefit_id"])
        if not benefit.multi_policy:
            domain = [
                ("employee_id", "=", vals["employee_id"]),
                ("benefit_id", "=", vals["benefit_id"]),
            ]
            if vals["start_date"] and not vals.get("end_date", False):
                domain = domain + [
                    "|",
                    ("end_date", "=", False),
                    ("end_date", ">=", vals["start_date"]),
                ]
            elif vals["start_date"] and vals["end_date"]:
                domain = domain + [
                    ("start_date", "<=", vals["end_date"]),
                    "|",
                    ("end_date", "=", False),
                    ("end_date", ">=", vals["start_date"]),
                ]

            policy_ids = self.search(domain)
            if len(policy_ids) > 0:
                raise UserError(
                    _(
                        "The employee is already enrolled in this benefit program."
                        "\n%s\nPolicy: %s"
                    )
                    % (policy_ids[0].employee_id.name, policy_ids[0].name)
                )

        # Check if eligibility requirements have been met
        if self._fail_eligibility(vals["benefit_id"], vals["employee_id"]):
            raise UserError(
                _(
                    "Eligibility Requirements Unmet. "
                    "The employee does not meet eligibility requirements for this benefit."
                )
            )

        ben_id = super(BenefitPolicy, self).create(vals)
        if ben_id:
            ref = self.env["ir.sequence"].next_by_code("benefit.policy.ref")
            if not ref:
                raise UserError(
                    _("Critical Error. " "Unable to obtain a benefit policy number!")
                )
            ben_id.name = ref
        return ben_id

    def unlink(self):

        for pol in self:
            if pol.state != "draft" and not (
                self.env.context and self.env.context.get("force_delete", False)
            ):
                raise UserError(
                    _(
                        'You may not delete a policy that is not in a "draft" state.'
                        "\nPolicy No: %s" % (pol.name)
                    )
                )

        return super(BenefitPolicy, self).unlink()

    def _check_state(self, to_state):
        for rec in self:
            if to_state == "draft" and rec.state not in ["", "draft"]:
                raise UserError(
                    _("You cannot set an open policy back to 'draft' state.")
                )
            elif to_state == "done" and rec.state != "open":
                raise UserError(
                    _("You cannot set an open policy back to 'draft' state.")
                )
            elif rec.state == "done":
                raise UserError(
                    _("You cannot set a policy in 'Done' state to any other value.")
                )

    def write(self, vals):
        if "state" in vals:
            self._check_state(vals["state"])
        return super(BenefitPolicy, self).write(vals)

    def state_open(self):

        self.write({"state": "open"})
        return True

    def state_done(self):

        self.write({"state": "done"})
        return True

    def end_policy(self):

        if len(self.ids) == 0:
            return False

        self.env.context.update({"end_benefit_policy_id": self.ids[0]})
        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.benefit.policy.end",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": self.env.context,
        }
