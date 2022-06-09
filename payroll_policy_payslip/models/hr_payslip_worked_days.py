# Copyright (C) 2013,2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrPayslipWorkedDays(models.Model):

    _inherit = "hr.payslip.worked_days"

    rate = fields.Float("Rate", required=True, default=0.0, digits="Payroll Rate")
    accrual_policy_line_id = fields.Many2one("hr.policy.line.accrual", "Accrual Policy")
