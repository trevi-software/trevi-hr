# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class BenefitClaim(models.Model):
    _name = "hr.benefit.claim"
    _description = "Benefit claim"
    _rec_name = "date"

    date = fields.Date(
        required=True,
        help="The date the claim was made",
        default=fields.Date.context_today,
    )
    benefit_policy_id = fields.Many2one(
        string="Policy",
        required=True,
        comodel_name="hr.benefit.policy",
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        required=True,
    )
    amount_requested = fields.Float(
        string="Requested Amount",
        digits="Account",
        required=True,
    )
    amount_approved = fields.Float(string="Approved Amount", digits="Account")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("approve", "Approved"),
            ("decline", "Declined"),
        ],
        default="draft",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="benefit_policy_id.company_id",
        store=True,
        index=True,
    )

    @api.depends("date", "benefit_policy_id")
    def _compute_display_name(self):
        # ``name_get`` was removed in Odoo 19; the display name is computed
        # explicitly instead.
        for rec in self:
            rec.display_name = f"{rec.benefit_policy_id.display_name} {rec.date}"

    @api.onchange("employee_id")
    def onchange_employee(self):
        res = {"domain": {"benefit_policy_id": False}}
        if not self.employee_id:
            return res

        res["domain"]["benefit_policy_id"] = [
            ("employee_id", "=", self.employee_id.id),
            ("benefit_id.has_advantage", "=", True),
        ]
        return res

    def _get_approved_amount(self, dDate):
        self.ensure_one()
        approved = 0.00
        if dDate:
            policy = self.benefit_policy_id
            d = dDate
            adv_line = policy.benefit_id.get_latest_advantage(d)
            if adv_line:
                remaining = adv_line.get_reimburse_remaining(self.employee_id, dDate)
                if adv_line.reim_nolimit:
                    # No limit
                    approved = self.amount_requested
                elif -1 == fields.Float.compare(remaining, 0.0, precision_digits=2):
                    # Over Limit
                    approved = 0.00
                else:
                    if -1 == fields.Float.compare(
                        remaining, self.amount_requested, precision_digits=2
                    ):
                        approved = remaining
                    else:
                        approved = self.amount_requested

        return approved

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.amount_approved = rec._get_approved_amount(rec.date)

        return records

    def _check_state(self, to_state):
        if self.state == "approve" and to_state == "draft":
            raise UserError(
                self.env._("You cannot set an approved claim back to 'draft' state.")
            )

    def write(self, vals):
        _fields = ["date", "employee_id", "amount_requested", "benefit_policy_id"]
        do_calc = False
        for k in vals:
            if k in _fields:
                do_calc = True
                break

        if "state" in vals:
            for clm in self:
                clm._check_state(vals["state"])

        res = super().write(vals)
        if do_calc:
            for clm in self:
                approved = clm._get_approved_amount(clm.date)
                clm.amount_approved = approved

        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_not_draft(self):
        data = self.read(["state"])
        for d in data:
            if d["state"] in ["approve", "decline"] and not (
                self.env.context and self.env.context.get("force_delete", False)
            ):
                raise UserError(
                    self.env._(
                        "Error: "
                        'You may not a delete a claim that is not in a "Draft" state'
                    )
                )

    def set_to_draft(self):
        self.state = "draft"
        return True

    def claim_approve(self):
        # Draft claims do not count towards the re-imbursement limit, so other
        # drafts may already have consumed part of it. Re-check the amount that
        # is still available at approval time, and approve the claims one at a
        # time so that a sibling in the same batch is taken into account.
        for clm in self:
            if clm.state == "approve":
                # Re-approving must not change an already saved amount.
                continue
            clm.amount_approved = clm._get_approved_amount(clm.date)
            clm.write({"state": "approve"})
        return True

    def claim_decline(self):
        self.write({"state": "decline"})
        return True
