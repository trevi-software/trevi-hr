# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BenefitClaim(models.Model):
    _name = "hr.benefit.claim"
    _description = "Benefit claim"
    _rec_name = "date"

    date = fields.Date(
        required=True,
        help="The date the claim was made",
        default=fields.Date.today(),
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

    def name_get(self):

        res = []
        data = self.read(["date", "benefit_policy_id"])
        for d in data:
            res.append((d["id"], d["benefit_policy_id"][1] + " " + str(d["date"])))
        return res

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
        for rec, vals in zip(records, vals_list, strict=True):
            approved = rec._get_approved_amount(vals["date"])
            rec.amount_approved = approved

        return records

    def _check_state(self, to_state):
        if self.state == "approve" and to_state == "draft":
            raise UserError(
                _("You cannot set an approved claim back to 'draft' state.")
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

    def unlink(self):

        data = self.read(["state"])
        for d in data:
            if d["state"] in ["approve", "decline"] and not (
                self.env.context and self.env.context.get("force_delete", False)
            ):
                raise UserError(
                    _(
                        "Error: "
                        'You may not a delete a claim that is not in a "Draft" state'
                    )
                )
        return super().unlink()

    def set_to_draft(self):
        self.state = "draft"
        return True

    def claim_approve(self):

        self.write({"state": "approve"})
        return True

    def claim_decline(self):

        self.write({"state": "decline"})
        return True
