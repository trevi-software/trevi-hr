# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SalaryRuleCategory(models.Model):
    _inherit = "hr.salary.rule.category"

    active = fields.Boolean(default=True)
