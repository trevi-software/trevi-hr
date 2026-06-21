# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class LeaveType(models.Model):

    _inherit = "hr.leave.type"
    _sql_constraints = [
        (
            "code_unique",
            "UNIQUE(company_id,code)",
            "Codes for leave type must be unique!",
        )
    ]

    code = fields.Char(required=True)
