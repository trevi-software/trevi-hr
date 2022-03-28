# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    dayoff_ids = fields.Many2many("resource.calendar.weekday", string="Days off")
    default_area_id = fields.Many2one("resource.schedule.area", "Default shift area")
    scheduled_shift_ids = fields.One2many("resource.schedule.shift", "resource_id")
    schedule_team_id = fields.Many2one("resource.schedule.team", "Shift team")

    def create_schedule(self, date_start, date_end, calendar=None):

        resources = self
        ScheduleShift = self.env["resource.schedule.shift"]
        return ScheduleShift.create_schedule(resources, date_start, date_end, calendar)
