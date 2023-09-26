# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PayrollRegister(models.Model):
    _inherit = "hr.payroll.register"

    operating_unit_id = fields.Many2one("operating.unit")
