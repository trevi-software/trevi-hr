# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    default_area_id = fields.Many2one(
        "resource.schedule.area",
        related="resource_id.default_area_id",
        string="Default shift area",
    )
    schedule_group_id = fields.Many2one("resource.schedule.group", "Scheduling group")
    scheduled_shift_ids = fields.One2many(
        "resource.schedule.shift", related="resource_id.scheduled_shift_ids"
    )

    def action_view_schedule(self):

        action_schedule = self.env.ref(
            "resource_schedule.open_employee_schedule_view"
        ).read()[0]
        action_schedule["context"] = {
            "search_default_resource_id": self.resource_id.id,
            "default_resource_id": self.resource_id.id,
        }
        return action_schedule

    def create_schedule(self, date_start, date_end, calendar=None):

        resources = self.mapped("resource_id")
        return resources.create_schedule(date_start, date_end, calendar)
