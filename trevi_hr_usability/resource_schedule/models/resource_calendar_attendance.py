# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
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
        string="Auto-punch",
        help="An attendance record will be created automatically for the resource.",
    )
    default_area_id = fields.Many2one("resource.schedule.area", check_company=True)
    schedule_group_ids = fields.Many2many("resource.schedule.group", check_company=True)
    resource_type = fields.Selection(
        related="resource_id.resource_type", readonly=True, store=True, index=True
    )
    shift_type = fields.Selection(
        selection=[("std", "Standard Shift"), ("flex", "Flex Shift")],
        default="std",
        required=True,
    )
    flex_core_from = fields.Float()
    flex_core_to = fields.Float()
    flex_scheduled_hrs = fields.Float(
        help="The resource must work this number of hours per day."
    )
    flex_scheduled_avg = fields.Boolean(
        help="If this option is checked scheduled hours denotes a daily average"
        "over a period of one week."
    )
    flex_weekly_hrs = fields.Float(
        help="If this value is set the resource must work this number of"
        "hours total during the week."
    )

    @api.constrains("shift_type", "autopunch")
    def _check_autopunch(self):
        for rec in self:
            if rec.shift_type == "flex" and rec.autopunch is True:
                raise ValidationError(_("Auto-punch cannot be used with a Flex Shift"))

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
                "shift_type": self.shift_type,
                "flex_scheduled_hrs": self.flex_scheduled_hrs,
                "flex_scheduled_avg": self.flex_scheduled_avg,
                "flex_core_from": self.flex_core_from,
                "flex_core_to": self.flex_core_to,
                "flex_weekly_hrs": self.flex_weekly_hrs,
            }
        )
        return res

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
            # flex_core_* must be 0 or larger than their respective hour_* values
            if rec.flex_core_from != 0 and rec.hour_from > rec.flex_core_from:
                rec.hour_from = rec.flex_core_from
            if rec.flex_core_to != 0 and rec.hour_to < rec.flex_core_to:
                rec.hour_to = rec.flex_core_to

            # _core_to must be larger than _core_from
            rec.flex_core_to = max(rec.flex_core_to, rec.flex_core_from)

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

    # This method was created to put all the possible ways of updating a
    # work record in one place. I don't like that it operates on self
    # sometimes and returns a dictionary other times. But I thought that
    # having it all in one method was better than scattered in _onchange()
    # and create() methods. During testing I kept repeatedly banging against
    # this problem because I would change the code in one place but forgot
    # the other place where the values were updated.
    #
    def _update_from_template(self, template, is_create=False, values=False):

        if values is False:
            values = {}
        if not template:
            return values
        if is_create is False:
            self.name = template.name
            self.shift_type = template.shift_type
            self.hour_from = template.hour_from
            self.hour_to = template.hour_to
            self.day_period = template.day_period
            self.span_midnight = template.span_midnight
            self.autopunch = template.autopunch
            self.flex_scheduled_hrs = template.flex_scheduled_hrs
            self.flex_scheduled_avg = template.flex_scheduled_avg
            self.flex_core_from = template.flex_core_from
            self.flex_core_to = template.flex_core_to
            self.flex_weekly_hrs = template.flex_weekly_hrs
        else:
            if "shift_type" not in values:
                values.update({"shift_type": template.shift_type})
            if "name" not in values:
                values.update({"name": template.name})
            if "hour_from" not in values:
                values.update({"hour_from": template.hour_from})
            if "hour_to" not in values:
                values.update({"hour_to": template.hour_to})
            if "day_period" not in values:
                values.update({"day_period": template.day_period})
            if "span_midnight" not in values:
                values.update({"span_midnight": template.span_midnight})
            if "autopunch" not in values:
                values.update({"autopunch": template.autopunch})
            if "flex_core_from" not in values:
                values.update({"flex_core_from": template.flex_core_from})
            if "flex_core_to" not in values:
                values.update({"flex_core_to": template.flex_core_to})
            if "flex_scheduled_hrs" not in values:
                values.update({"flex_scheduled_hrs": template.flex_scheduled_hrs})
            if "flex_scheduled_avg" not in values:
                values.update({"flex_scheduled_avg": template.flex_scheduled_avg})
            if "flex_weekly_hrs" not in values:
                values.update({"flex_weekly_hrs": template.flex_weekly_hrs})
        return values

    @api.onchange("template_id")
    def _onchange_template_id(self):
        for rec in self:
            tpl = rec.template_id
            if tpl:
                rec._update_from_template(tpl)

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
            if (
                "shift_type" in values
                and values["shift_type"] == "flex"
                and "autopunch" in values
                and values["autopunch"] is True
            ):
                raise ValidationError(_("Auto-punch cannot be used with a Flex Shift"))

            if "template_id" in values:
                tpl = self.env["resource.calendar.attendance.template"].browse(
                    values["template_id"]
                )
                res = self._update_from_template(tpl, is_create=True, values=values)
                values.update(res)

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
