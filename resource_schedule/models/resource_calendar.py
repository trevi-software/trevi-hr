# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResourceCalendar(models.Model):

    _inherit = "resource.calendar"

    dayoff_type = fields.Selection(
        [
            ("fix_all", "Fixed for all"),
            ("fix_one", "Fixed individualy"),
            ("rolling", "Rolling weekly"),
        ],
        default="fix_all",
        string="Day off type",
        help="""
        Fixed for all - the unscheduled days in the working time apply to all resources.
        Fixed individually - the days off will be specified in each resource's record. If
        it is not, the default days off will be used.
        Rolling weekly - each reasource's day(s) off changes on a weekly basis. For
        example, if the resource was off on Saturday last week, this week it will be
        Friday, and next week it will be Thursday.
        """,
    )
    default_dayoff_ids = fields.Many2many(
        "resource.calendar.weekday", string="Days off"
    )

    @api.model
    def default_get(self, fields):

        res = super().default_get(fields)

        # Inject the default work detail templates into the default values
        #
        if "attendance_ids" in fields and res.get("attendance_ids", False):
            morning = self.env.ref("resource_schedule.attendance_template_0")
            afternoon = self.env.ref("resource_schedule.attendance_template_1")
            company_id = res.get("company_id", self.env.company.id)
            company = self.env["res.company"].browse(company_id)
            company_attendance_ids = company.resource_calendar_id.attendance_ids
            if company_attendance_ids:
                for i, attendance in enumerate(company_attendance_ids):
                    if attendance.template_id:
                        res["attendance_ids"][i][2].update(
                            {"template_id": attendance.template_id.id}
                        )
            else:
                for line in res["attendance_ids"]:
                    if line[2]["hour_from"] == 8:
                        line[2].update({"template_id": morning.id})
                    elif line[2]["hour_from"] == 13:
                        line[2].update({"template_id": afternoon.id})

        return res

    @api.onchange("attendance_ids")
    def _onchange_attendance_ids(self):

        section_ids = self.attendance_ids.filtered(
            lambda a: a.display_type == "line_section"
        )
        if self.two_weeks_calendar and len(section_ids) > 2:
            for line in self.attendance_ids:
                wtype = (line.week_nbr % 2) == 0 and "0" or "1"
                line.week_type = wtype
        else:
            super()._onchange_attendance_ids()

    @api.constrains("attendance_ids")
    def _check_attendance(self):

        filtered = self.env["resource.calendar"]
        for calendar in self:
            # For the moment, don't check work items that contain a night shift
            #
            if calendar.attendance_ids.filtered(lambda att: att.span_midnight):
                continue

            # Check multi-week calendars because the _check_overlap() method in the
            # parent class expects to check only 2 weeks
            if calendar.two_weeks_calendar:
                section_ids = calendar.attendance_ids.filtered(
                    lambda att: att.display_type == "line_section"
                )
                attendance_ids = calendar.attendance_ids.filtered(
                    lambda attendance: not attendance.resource_id
                    and attendance.display_type is False
                )
                week_list = section_ids.mapped("week_nbr")
                for nbr in week_list:
                    attendances = attendance_ids.filtered(
                        lambda attendance: attendance.week_nbr == nbr
                    )
                    if attendances:
                        calendar._check_overlap(attendances)
                continue

            # Pass on all the rest
            filtered |= calendar

        return super(ResourceCalendar, filtered)._check_attendance()

    # Over-ride parent class method to handle more than two weeks and flex schedule
    def _compute_hours_per_day(self, attendances):
        if not attendances:
            return super()._compute_hours_per_day(attendances)

        hour_count = 0.0
        for attendance in attendances:
            if attendance.shift_type != "flex":
                hour_count += attendance.hour_to - attendance.hour_from
            elif attendance.shift_type == "flex":
                hour_count += attendance.flex_scheduled_hrs
            if (
                attendance.shift_type != "flex"
                and attendance.template_id
                and attendance.template_id.autodeduct_break
            ):
                hour_count -= float(attendance.template_id.break_minutes) / 60.0

        number_of_days = 0
        dayofweek = False
        for att in attendances.sorted("sequence"):
            if dayofweek is False or att.dayofweek != dayofweek:
                number_of_days += 1
                dayofweek = att.dayofweek
        return fields.Float.round(
            hour_count / float(number_of_days), precision_digits=2
        )

    def switch_calendar_type(self):

        super().switch_calendar_type()

        if not self.two_weeks_calendar:
            return

        for att in self.attendance_ids:
            if att.sequence < 25:
                if att.sequence == 0:
                    att.name = _("Week 0")
                att.week_nbr = 0
            else:
                if att.sequence == 25:
                    att.name = _("Week 1")
                att.week_nbr = 1

    def get_rest_days(self):
        """If the rest day(s) have been explicitly specified that's what is returned, otherwise
        a guess is returned based on the week days that are not scheduled. If an explicit
        rest day(s) has not been specified an empty list is returned. If it is able to figure
        out the rest days it will return a list of week day integers with Monday being 0."""

        res = []
        for tpl in self:
            if tpl.restday_ids:
                res = [rd.sequence for rd in tpl.restday_ids]
            else:
                weekdays = ["0", "1", "2", "3", "4", "5", "6"]
                scheddays = []
                scheddays = [
                    wt.dayofweek
                    for wt in tpl.attendance_ids
                    if wt.dayofweek not in scheddays
                ]
                res = [int(d) for d in weekdays if d not in scheddays]
                # If there are no work days return nothing instead of *ALL* the days in the week
                if len(res) == 7:
                    res = []

        return res

    @api.model
    def get_hours_by_weekday(self, tpl, day_no):
        """Return the number working hours in the template for day_no.
        For day_no 0 is Monday."""

        delta = timedelta(seconds=0)
        for worktime in tpl.worktime_ids:
            if int(worktime.dayofweek) != day_no:
                continue

            fromHour, fromSep, fromMin = worktime.hour_from.partition(":")
            toHour, toSep, toMin = worktime.hour_to.partition(":")
            if len(fromSep) == 0 or len(toSep) == 0:
                raise ValidationError(_("Format of working hours is incorrect"))

            delta += datetime.strptime(
                toHour + ":" + toMin, "%H:%M"
            ) - datetime.strptime(fromHour + ":" + fromMin, "%H:%M")

        return float(delta.seconds / 60) / 60.0
