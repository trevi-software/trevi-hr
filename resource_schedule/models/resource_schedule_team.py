# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResourceScheduleTeam(models.Model):

    _name = "resource.schedule.team"
    _description = "Scheduling Shift Team"

    name = fields.Char()
    resource_ids = fields.One2many("resource.resource", "schedule_team_id", "Resources")
    resource_count = fields.Integer(compute="_compute_resource_count")
    resource_calendar_id = fields.Many2one("resource.calendar", "Working Times")
    start_week = fields.Integer(
        default=0,
        help="In multi-week schedule rotation this denotes the week number on"
        "which this team will start the rotation. In single week schedules leave"
        "this value at 0.",
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color Index")
    scheduled_shift_ids = fields.One2many(
        "resource.schedule.shift", "schedule_team_id", "Scheduled Shifts"
    )

    def _compute_resource_count(self):
        for team in self:
            team.resource_count = len(team.resource_ids)
