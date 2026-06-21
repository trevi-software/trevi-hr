# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
            ("8day", "Work day"),
            ("12day", "All day"),
            ("12night", "All night"),
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
    shift_type = fields.Selection(
        selection=[("std", "Standard"), ("flex", "Flex Shift")],
        default="std",
        required=True,
    )
    flex_core_from = fields.Float(default=0)
    flex_core_to = fields.Float(default=0)
    flex_scheduled_hrs = fields.Float()
    flex_scheduled_avg = fields.Boolean(
        help="If this option is checked scheduled hours denotes a daily average"
        "over a period of one week."
    )
    flex_weekly_hrs = fields.Float(
        help="If this value is set the resource must work this number of"
        "hours total during the week."
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company)

    @api.constrains("shift_type", "autopunch")
    def _check_autopunch(self):
        for rec in self:
            if rec.shift_type == "flex" and rec.autopunch is True:
                raise ValidationError(_("Auto-punch cannot be used with a Flex Shift"))

    @api.constrains("shift_type", "autodeduct_break")
    def _check_autodeduct_break(self):
        for rec in self:
            if rec.shift_type == "flex" and rec.autodeduct_break is True:
                raise ValidationError(
                    _("Auto-deduct break time cannot be used with a Flex Shift")
                )

    @api.onchange("flex_scheduled_hrs")
    def _onchange_flex_scheduled_hrs(self):
        for rec in self:
            if rec.flex_scheduled_hrs < 0:
                rec.flex_scheduled_hrs = 0
            elif rec.flex_scheduled_hrs > 24:
                rec.flex_scheduled_hrs = 24

    @api.onchange("flex_core_from", "flex_core_to", "hour_from", "hour_to")
    def _onchange_flex(self):
        for rec in self:
            if rec.flex_core_from != 0 and rec.hour_from > rec.flex_core_from:
                rec.hour_from = rec.flex_core_from
            if rec.flex_core_to != 0 and rec.hour_to < rec.flex_core_to:
                rec.hour_to = rec.flex_core_to
            if rec.flex_core_from != 0 and rec.flex_core_to != 0:
                if rec.flex_core_to < rec.flex_core_from:
                    rec.flex_core_to = rec.flex_core_from
