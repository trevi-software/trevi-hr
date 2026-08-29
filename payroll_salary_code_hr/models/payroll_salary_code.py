# Copyright (C) 2025 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PayrollSalaryCode(models.Model):
    _inherit = "payroll.salary.code"

    contract_ids = fields.One2many(
        string="Contracts",
        comodel_name="hr.contract",
        inverse_name="payroll_salary_code",
        help="Contracts the salary code is assigned to.",
    )
