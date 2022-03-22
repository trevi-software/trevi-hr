# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ContractInit(models.Model):

    _inherit = "hr.contract.init"

    resource_calendar_id = fields.Many2one(
        "resource.calendar",
        "Working Hours",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
