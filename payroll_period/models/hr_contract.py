# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Contract(models.Model):
    _inherit = "hr.contract"

    pps_id = fields.Many2one("hr.payroll.period.schedule", required=True)
