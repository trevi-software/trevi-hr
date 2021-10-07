# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ResConfig(models.TransientModel):

    _inherit = "res.config.settings"

    concurrent_contracts = fields.Boolean(
        string="Allow concurrent contracts",
        config_parameter="hr_contract_state.concurrent_contracts",
        default=False,
        help="Allow multiple concurrent contracts for an employee",
    )
