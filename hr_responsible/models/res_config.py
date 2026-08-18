# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    hr_responsible = fields.Boolean(
        string="Default HR Responsible",
        config_parameter="hr_responsible.hr_responsible",
        default=False,
        help="Set the default HR responsible for employees",
    )
