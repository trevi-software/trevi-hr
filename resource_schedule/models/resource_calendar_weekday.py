# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResourceCalendarWeekday(models.Model):

    _name = "resource.calendar.weekday"
    _description = "Calendar Weekdays"

    name = fields.Char(required=True)
    dayofweek = fields.Char(required=True)
