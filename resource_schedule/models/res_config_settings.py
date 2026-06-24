# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    max_shift_length = fields.Integer(
        string="Maximum Shift Length",
        config_parameter="resource_schedule.max_shift_length",
    )
