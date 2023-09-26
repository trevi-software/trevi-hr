# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrJob(models.Model):

    _inherit = "hr.job"

    default_area_id = fields.Many2one("resource.schedule.area", "Default shift area")
