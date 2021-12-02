# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PremiumPayment(models.Model):

    _name = "hr.benefit.premium.payment"
    _description = "Benefit premium payment"
    _rec_name = "date"

    def _compute_policy_id_domain(self):
        policy_ids = self.env["hr.benefit.policy"].search(
            [
                ("employee_id", "in", self.mapped("employee_id").ids),
            ]
        )
        policy_ids = policy_ids.filtered(lambda rec: rec.benefit_id.has_premium)
        return [("id", "in", policy_ids.ids)]

    date = fields.Date(required=True, default=fields.Date.today())
    policy_id = fields.Many2one(
        string="Policy",
        comodel_name="hr.benefit.policy",
        domain=_compute_policy_id_domain,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    amount = fields.Float(
        digits="Account",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    payslip_id = fields.Many2one(
        string="Payslip", comodel_name="hr.payslip", ondelete="cascade"
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("cancel", "Cancelled"),
            ("done", "Done"),
        ],
        readonly=True,
        default="draft",
    )

    def name_get(self):

        res = []
        for payment in self:
            res.append(
                (
                    payment.id,
                    "{} {} {}".format(
                        payment.policy_id.name, payment.date, payment.amount
                    ),
                )
            )

        return res

    def unlink(self):

        for payment in self:
            if payment.state != "draft" and not (
                payment.env.context and payment.env.context.get("force_delete", False)
            ):
                raise UserError(
                    _(
                        "Permission Denied"
                        'You may not delete a premium payment that is past the "draft" stage.'
                        "\nPolicy: %s\nPayment Date: %s"
                    )
                    % (payment.policy_id.name, payment.date)
                )

        return super(PremiumPayment, self).unlink()

    def state_pending(self):

        return self.write({"state": "pending"})

    def state_done(self):

        return self.write({"state": "done"})

    def state_cancel(self):

        return self.write({"state": "cancel"})
