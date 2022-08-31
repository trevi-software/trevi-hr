# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PayrollPeriodSchedule(models.Model):
    _inherit = "hr.payroll.period.schedule"

    batch_by_contract_type = fields.Boolean(
        help="If checked create payslip batches by contract type."
    )
