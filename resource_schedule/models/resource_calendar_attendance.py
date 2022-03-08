# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools.float_utils import float_split


class ResourceCalendarAttendance(models.Model):

    _inherit = "resource.calendar.attendance"
    _order = "sequence, week_nbr, dayofweek, hour_from"

    day_period = fields.Selection(
        selection_add=[
            ("morning",),
            ("afternoon",),
            ("evening", "Evening"),
            ("8day", "8 Hour Day"),
            ("12day", "12 Hour Day"),
            ("12night", "12 Hour Night"),
        ],
        ondelete={
            "evening": "set default",
            "8day": "set default",
            "12day": "set default",
            "12night": "set default",
        },
    )
    template_id = fields.Many2one("resource.calendar.attendance.template")
    week_nbr = fields.Integer(
        string="Week", help="The week number in the weekly rotation"
    )
    duration = fields.Integer(
        compute="_compute_duration",
        store=True,
        readonly=True,
        help="Duration of period in seconds",
    )
    span_midnight = fields.Boolean(
        help="This shift crosses over midnight into a new day."
    )
    autopunch = fields.Boolean(
        help="An attendance record will be created automatically for the resource."
    )
    default_area_id = fields.Many2one("resource.schedule.area", check_company=True)
    schedule_group_ids = fields.Many2many("resource.schedule.group", check_company=True)
    resource_type = fields.Selection(
        related="resource_id.resource_type", readonly=True, store=True, index=True
    )

    # Over-ride inherited method to take into account shifts that span midnight.
    @api.onchange("hour_from", "hour_to")
    def _onchange_hours(self):
        if not self.span_midnight:
            return super()._onchange_hours()

        # avoid negative or after midnight
        self.hour_from = min(self.hour_from, 23.99)
        self.hour_from = max(self.hour_from, 0.0)
        self.hour_to = min(self.hour_to, 23.99)
        self.hour_to = max(self.hour_to, 0.0)

    def _copy_attendance_vals(self):
        self.ensure_one()
        res = super()._copy_attendance_vals()
        res.update(
            {
                "template_id": self.template_id.id,
                "span_midnight": self.span_midnight,
                "autopunch": self.autopunch,
                "default_area_id": self.default_area_id.id,
                "schedule_group_ids": [(6, 0, [g.id for g in self.schedule_group_ids])],
            }
        )
        return res

    @api.onchange("sequence")
    def _onchange_sequence(self):

        for rec in self:
            if not rec.calendar_id:
                continue
            sections = rec.calendar_id.attendance_ids.filtered(
                lambda a: a.display_type == "line_section"
                and a.sequence <= rec.sequence
            ).sorted("sequence")
            if sections and sections[-1].sequence == rec.sequence:
                # If workday was moved into the place of a section header, the section
                # header sequence hasn't been bumped up yet so it will match the
                # above filter
                if len(sections) > 1:
                    rec.week_nbr = sections[-2].week_nbr
                    rec._onchange_week_nbr()
            elif sections:
                rec.week_nbr = sections[-1].week_nbr

    @api.onchange("week_nbr")
    def _onchange_week_nbr(self):

        for rec in self:
            rec.week_type = rec.week_nbr % 2 == 0 and "0" or "1"

    @api.model
    def _compute_duration_common(self, hour_from, hour_to, span_midnight=False):
        if not span_midnight:
            hours, mins = float_split(hour_to - hour_from, precision_digits=2)
            mins = int(mins * 60 / 100)
        else:
            hours, mins = float_split(hour_to - 0, precision_digits=2)
            _hours, _mins = float_split(24 - hour_from, precision_digits=2)
            hours += _hours
            mins += _mins
        return (hours * 60 * 60) + (mins * 60)

    @api.depends("hour_from", "hour_to")
    def _compute_duration(self):

        for rec in self:
            _duration = rec._compute_duration_common(
                rec.hour_from, rec.hour_to, rec.span_midnight
            )
            if rec.template_id and rec.template_id.autodeduct_break:
                rec.duration = _duration - (rec.template_id.break_minutes * 60)
            else:
                rec.duration = _duration

    @api.onchange("template_id")
    def _onchange_template_id(self):
        for rec in self:
            tpl = rec.template_id
            if tpl:
                rec.name = tpl.name
                rec.hour_from = tpl.hour_from
                rec.hour_to = tpl.hour_to
                rec.day_period = tpl.day_period
                rec.span_midnight = tpl.span_midnight
                rec.autopunch = tpl.autopunch

    def _fix_week_nbr(self):
        self.ensure_one()

        sections = self.calendar_id.attendance_ids.filtered(
            lambda a: a.display_type == "line_section"
        )

        if len(sections) == 0:
            # Single week
            self.week_nbr = 0
        else:
            # Multi-week
            prev_att = False
            for att in self.calendar_id.attendance_ids.sorted("sequence"):
                if att.display_type == "line_section":
                    prev_att = att
                    continue
                if att == self:
                    break
                prev_att = att
            if prev_att is False:
                self.week_nbr = 0
            else:
                self.week_nbr = prev_att.week_nbr

    @api.model_create_multi
    def create(self, values_list):

        for values in values_list:
            if "template_id" in values:
                tpl = self.env["resource.calendar.attendance.template"].browse(
                    values["template_id"]
                )
                if "name" not in values:
                    values.update({"name": tpl.name})
                if "hour_from" not in values:
                    values.update({"hour_from": tpl.hour_from})
                if "hour_to" not in values:
                    values.update({"hour_to": tpl.hour_to})
                if "day_period" not in values:
                    values.update({"day_period": tpl.day_period})
                if "span_midnight" not in values:
                    values.update({"span_midnight": tpl.span_midnight})
                if "autopunch" not in values:
                    values.update({"autopunch": tpl.autopunch})

        res = super().create(values_list)

        # First, set the week number for section headers. Keep in mind the created
        # records may not all belong to the same calendar.
        for rec in res.filtered(lambda a: a.display_type == "line_section").sorted(
            "sequence"
        ):
            for idx, att in enumerate(
                rec.calendar_id.attendance_ids.filtered(
                    lambda a: a.display_type == "line_section"
                )
            ):
                att.week_nbr = idx

        # Handle work days
        for rec in res.filtered(lambda a: a.display_type is False).sorted("sequence"):
            rec._fix_week_nbr()
            rec.week_type = rec.week_nbr % 2 == 0 and "0" or "1"

        return res

    def write(self, values):

        res = super().write(values)
        if "sequence" in values:
            self._onchange_sequence()
        return res
