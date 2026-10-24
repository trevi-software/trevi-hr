# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class PremiumPayment(models.Model):
    _name = "hr.benefit.premium.payment"
    _description = "Benefit premium payment"
    _rec_name = "date"

    date = fields.Date(required=True, default=fields.Date.today)
    policy_id = fields.Many2one(
        comodel_name="hr.benefit.policy",
        # A server-side callable is evaluated on an empty recordset while the
        # field is being described, so it always yields an empty list and never
        # reacts to the employee chosen in the form. A client-side domain
        # string refers to the form's ``employee_id`` and is re-evaluated when
        # that field changes.
        domain=(
            "[('employee_id', '=', employee_id), ('benefit_id.has_premium', '=', True)]"
        ),
        required=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        required=True,
    )
    amount = fields.Float(
        digits="Account",
        required=True,
    )
    payslip_id = fields.Many2one(comodel_name="hr.payslip", ondelete="cascade")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("cancel", "Cancelled"),
            ("done", "Done"),
        ],
        default="draft",
    )

    def _compute_display_name(self):
        for payment in self:
            payment.display_name = (
                f"{payment.policy_id.name} {payment.date} {payment.amount}"
            )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_non_draft(self):
        for payment in self:
            if payment.state != "draft" and not (
                payment.env.context and payment.env.context.get("force_delete", False)
            ):
                raise UserError(
                    self.env._(
                        "Permission Denied. "
                        "You may not delete a payment that is not in 'draft' stage."
                        "\nPolicy: %(name)s\nPayment Date: %(date)s",
                        name=payment.policy_id.name,
                        date=payment.date,
                    )
                )

    def action_pending(self):
        return self.write({"state": "pending"})

    def action_done(self):
        return self.write({"state": "done"})

    def action_cancel(self):
        return self.write({"state": "cancel"})
