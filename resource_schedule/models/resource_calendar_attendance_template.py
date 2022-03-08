# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResourceCalendarAttendanceTemplate(models.Model):

    _name = "resource.calendar.attendance.template"
    _description = "Work Detail Template"

    name = fields.Char(required=True)
    hour_from = fields.Float(string="Work from", required=True, index=True)
    hour_to = fields.Float(string="Work to", required=True)
    day_period = fields.Selection(
        selection=[
            ("morning", "Morning"),
            ("afternoon", "Afternoon"),
            ("evening", "Evening"),
            ("8day", "8 Hour Day"),
            ("12day", "12 Hour Day"),
            ("12night", "12 Hour Night"),
        ],
        required=True,
    )
    span_midnight = fields.Boolean(
        help="This shift crosses over midnight into a new day."
    )
    auto_splitshift = fields.Boolean(
        string="Automatically split shifts at midnight",
        help="When a shift crosses over into a new calendar day close out the"
        "current shift and start a new shift.",
    )
    autopunch = fields.Boolean(
        help="An attendance record will be created automatically for the resource."
    )
    autodeduct_break = fields.Boolean(string="Auto-deduct break")
    break_minutes = fields.Integer(
        help="The number of minutes to deduct for breaks from the scheduled time."
    )
    default_area_id = fields.Many2one("resource.schedule.area")
    schedule_group_ids = fields.Many2many(
        "resource.schedule.group", "resource_attendance_template_schedule_group_rel"
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company)
