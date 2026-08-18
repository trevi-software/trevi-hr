# Copyright (C) 2024 Trevi Software (https://trevi.et)
# Copyright (C) 2024 Michael Telahun Makonnen <telahunmike@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    certificate = fields.Selection(selection_add=[("diploma", "Diploma")])
