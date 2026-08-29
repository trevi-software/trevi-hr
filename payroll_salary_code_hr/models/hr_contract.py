# Copyright (C) 2025 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    payroll_salary_code = fields.Many2one(
        comodel_name="payroll.salary.code",
        help="Salary code assigned to this contract.",
    )
