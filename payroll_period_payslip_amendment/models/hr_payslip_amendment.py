# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PayslipAmendment(models.Model):
    _inherit = "hr.payslip.amendment"

    period_id = fields.Many2one(
        string="Payroll Period",
        comodel_name="hr.payroll.period",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.onchange("period_id")
    def _onchange_period_id(self):
        for rec in self:
            rec.date = rec.period_id.date_end
