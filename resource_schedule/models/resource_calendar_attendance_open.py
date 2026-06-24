# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResourceCalendarShiftTemplateOpen(models.Model):
    _name = "resource.calendar.attendance.open"
    _inherit = "resource.calendar.attendance"
    _description = "Resource Open Shift Template"

    available = fields.Integer(help="The number of shifts available for pickup.")
