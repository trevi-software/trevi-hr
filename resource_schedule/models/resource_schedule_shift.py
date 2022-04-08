# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.resource.models.resource import float_to_time


class ResourceScheduleShift(models.Model):

    _name = "resource.schedule.shift"
    _inherit = "resource.calendar.attendance"
    _description = "Resource Shift"
    _order = "datetime_start"
    _check_company_auto = True

    calendar_id = fields.Many2one(ondelete="restrict")
    name = fields.Char(
        compute="_compute_name", required=False, readonly=True, store=True
    )
    hour_from = fields.Float(
        compute="_compute_name", required=False, index=False, store=True
    )
    hour_to = fields.Float(
        compute="_compute_name", required=False, index=False, store=True
    )
    autopunch = fields.Boolean(index=True)
    datetime_start = fields.Datetime(string="Start", required=True)
    datetime_end = fields.Datetime(string="End", required=True)
    day = fields.Date(compute="_compute_name", store=True, index=True)
    employee_id = fields.Many2one(
        "hr.employee",
        compute="_compute_employee_id",
        store=True,
        index=True,
        check_company=True,
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
        related="employee_id.department_id",
        store=True,
        check_company=True,
    )
    schedule_team_id = fields.Many2one(
        "resource.schedule.team", related="resource_id.schedule_team_id", string="Team"
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    tz = fields.Selection(
        related="resource_id.tz",
        default=lambda self: self._context.get("tz") or self.env.user.tz or "UTC",
        readonly=True,
        store=True,
    )
    published = fields.Boolean(string="Publish")
    hr_attendance_ids = fields.One2many(
        "hr.attendance", "schedule_shift_id", "Attendance Records"
    )

    def name_get(self):

        HOUR_FORMAT = "%I:%M %p"
        res = []
        for rec in self:
            if not rec.datetime_start or not rec.datetime_end:
                continue
            local_tz = timezone(rec.tz)
            tzDtStart = utc.localize(rec.datetime_start, is_dst=False).astimezone(
                local_tz
            )
            tzDtEnd = utc.localize(rec.datetime_end, is_dst=False).astimezone(local_tz)
            strFrom = tzDtStart.strftime(HOUR_FORMAT)
            strTo = tzDtEnd.strftime(HOUR_FORMAT)
            mins, _secs = divmod(rec.duration, 60)
            hours, mins = divmod(mins, 60)
            res.append((rec.id, f"{strFrom} - {strTo} ({hours}h{mins}m)"))

        return res

    # https://www.odoo.com/forum/help-1/convert-hours-and-minute-into-float-value-168236
    @api.model
    def time2float(self, value):
        vals = value.split(":")
        t, hours = divmod(float(vals[0]), 24)
        t, minutes = divmod(float(vals[1]), 60)
        minutes = minutes / 60.0
        return hours + minutes

    @api.depends("datetime_start", "datetime_end")
    def _compute_name(self):

        for rec in self:
            if not rec.datetime_start or not rec.datetime_end:
                continue
            rec.name = rec.name_get()[0][1]
            rec.day = rec.datetime_start.date()
            rec.hour_from = rec.time2float(
                rec.localize_dt(rec.datetime_start, rec.tz).strftime("%H:%M")
            )
            rec.hour_to = rec.time2float(
                rec.localize_dt(rec.datetime_end, rec.tz).strftime("%H:%M")
            )
        return

    @api.depends("resource_id")
    def _compute_employee_id(self):
        for shift in self:
            employee = self.env["hr.employee"].search(
                [("resource_id", "=", shift.resource_id.id)],
                limit=1,
            )
            shift.employee_id = employee

    def _update_default_area(self):
        for rec in self:
            # Default area on resource takes precedence.
            if rec.resource_id.default_area_id:
                rec.default_area_id = rec.resource_id.default_area_id
            elif rec.template_id.default_area_id:
                rec.default_area_id = rec.template_id.default_area_id

    # Over-ride behaviour in parent class
    # @api.depends("template_id")
    # def _onchange_template_id(self):
    #     return

    @api.onchange("resource_id")
    def onchange_resource_id(self):
        for rec in self:
            rec.calendar_id = rec.resource_id.calendar_id
            rec._update_default_area()

    @api.onchange("calendar_id")
    def onchange_calendar_id(self):
        for rec in self:
            today = date.today()
            if rec.datetime_start:
                today = rec.datetime_start.date()
            if rec.calendar_id:
                attendance = False
                for detail in rec.calendar_id.attendance_ids:
                    if detail.dayofweek == str(today.weekday()):
                        attendance = detail
                        break
                if attendance:
                    dtStart = datetime.combine(
                        today, float_to_time(attendance.hour_from)
                    )
                    dtEnd = datetime.combine(today, float_to_time(attendance.hour_to))
                    dtStart = self.localize_dt(dtStart, rec.tz, reverse=True)
                    dtEnd = self.localize_dt(dtEnd, rec.tz, reverse=True)
                    rec.template_id = attendance.template_id
                    rec.day_period = attendance.day_period
                    rec.datetime_start = dtStart
                    rec.datetime_end = dtEnd
                    rec.dayofweek = str(dtStart.date().weekday())
                else:
                    rec.template_id = False
                    rec.day_period = False
                    rec.dayofweek = str(today.weekday())
                    rec.hour_from = False
                    rec.hour_to = False

    @api.onchange("template_id")
    def onchange_template_id(self):
        for rec in self:
            rec._update_default_area()

    def datetimes_naive_utc(self):

        res = [shift._datetimes_naive_utc() for shift in self]
        return res

    def _datetimes_naive_utc(self):

        self.ensure_one()
        return (self.datetime_start, self.datetime_end, self)

    def datetimes_naive_tz(self):

        res = [shift._datetimes_naive_tz() for shift in self]
        return res

    def _datetimes_naive_tz(self):

        self.ensure_one()
        ltz = timezone(self.tz)
        return (
            utc.localize(self.datetime_start, is_dst=False)
            .astimezone(ltz)
            .replace(tzinfo=None),
            utc.localize(self.datetime_end, is_dst=False)
            .astimezone(ltz)
            .replace(tzinfo=None),
            self,
        )

    @api.model
    def localize_dt(self, dt, tz, reverse=False):
        """
        Localize naive dt from database (UTC) to timzezone tz. If reverse is True
        a naive dt that is in timezone tz is converted to naive dt for storage in db.
        """

        local_tz = timezone(tz)
        if not reverse:
            res = utc.localize(dt, is_dst=False).astimezone(local_tz)
        else:
            res = (
                local_tz.localize(dt, is_dst=False).astimezone(utc).replace(tzinfo=None)
            )
        return res

    @api.model
    def get_daysoff(self, resource, calendar, date_start, date_end):
        def _get_preceding_weekday(day_list):
            _d = int(day_list[-1])
            _daysoff = []
            # Rolling days off means every 7 weeks both monday and sunday are off.
            # If we get either in a  week it means both. So, saturday is next.
            if _d in [0, 6]:
                _daysoff = ["5"]
            elif _d == 1:
                # Same as above. If last week was tuesday, this week is mon & sun
                _daysoff = ["0", "6"]
            else:
                _daysoff = [str(_d - 1)]
            return _daysoff

        res = []
        weeks = abs(date_end - date_start).days // 7 + 2
        if calendar.dayoff_type == "fix_one":
            daysoff = calendar.default_dayoff_ids.mapped("dayofweek")
            if len(resource.dayoff_ids) > 0:
                daysoff = resource.dayoff_ids.mapped("dayofweek")
            for _i in range(weeks):
                res.append(daysoff)
        elif calendar.dayoff_type == "rolling":
            # Was there a day off within the last
            # 7 days? If so, move backward one day. Otherwise, use the
            # default days in the resource or the working times.
            #
            daysoff = []
            week_list = ["0", "1", "2", "3", "4", "5", "6"]
            date_lastweek = date_start - timedelta(days=7)
            shifts = self.search(
                [
                    ("resource_id", "=", resource.id),
                    ("datetime_start", "<", date_start),
                    ("datetime_start", ">=", date_lastweek),
                ],
            )
            if len(shifts) > 0:
                _tmp = shifts.mapped("dayofweek")
                daysoff = [x for x in week_list if x not in _tmp]
                daysoff = _get_preceding_weekday(daysoff)
            else:
                if len(resource.dayoff_ids) > 0:
                    daysoff = resource.dayoff_ids.mapped("dayofweek")
                else:
                    daysoff = calendar.default_dayoff_ids.mapped("dayofweek")

            # Set the days off for the rest of the weeks
            #
            res.append(daysoff)
            for _i in range(weeks - 1):
                daysoff = _get_preceding_weekday(daysoff)
                res.append(daysoff)

        else:
            # Fixed day off for all
            for _i in range(weeks):
                res.append([])

        return res

    @api.model
    def autopunch_shifts(self):
        now = fields.Datetime.now()
        return self._autopunch_shifts(now)

    @api.model
    def _autopunch_shifts(self, now):

        res = self.env["hr.attendance"]
        dToday = now.date()
        dLastRun = dToday
        today = False

        # Begin creating autopunches from the last time this code ran
        lastrun = self.env["resource.schedule.autopunch.lastrun"].search([], limit=1)
        if len(lastrun) > 0:
            dLastRun = lastrun.name.date()
        if dLastRun < dToday:
            today = dLastRun
        elif dLastRun == dToday:
            today = dToday
        else:
            return res

        while today <= dToday:
            _now = now
            if today < dToday:
                _now = datetime.combine(today, datetime.max.time())

            shifts = self.search(
                [
                    ("autopunch", "=", True),
                    ("day", "=", today),
                ]
            )
            employees = shifts.mapped("employee_id")
            for ee in employees:
                details = shifts.filtered(lambda sh: sh.employee_id == ee)
                if len(details) == 0:
                    continue

                res |= self.check_and_create_autopunch(ee, details, _now)

            today += timedelta(days=1)

        # Log this run
        self.env["resource.schedule.autopunch.lastrun"].create(
            {
                "name": now,
                "record_ids": [(6, 0, res.ids)],
            }
        )

        return res.sorted(None)

    @api.model
    def check_and_create_autopunch(self, employee, details, now):
        """Checks for attendance records that match the details given and if none
        exist it will create attendance records according to those details. If any
        are created it will return the records created.
        :param employee: the employee whose shift schedule to check
        :type employee: :class:`~hr.employee`
        :param :class:`~resource.schedule.shift` details: The work details to check
        :param datetime now: the current UTC datetime in naive datetime format.
        :returns: :class:`~hr.attendance`
        """

        res = self.env["hr.attendance"]
        details = details.filtered(lambda d: d.autopunch is True)
        if not details:
            return res

        # We assume details are in correct order
        dtStart = details[0].datetime_start
        dtEnd = details[-1].datetime_end

        # Are there already attendance records for today?
        punches = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", employee.id),
                ("check_in", ">=", dtStart),
                ("check_in", "<", dtEnd),
                "|",
                ("check_out", "=", False),
                ("check_out", "<", dtEnd),
            ]
        )

        HrAttendance = self.env["hr.attendance"]

        # No attendance, do all up to now
        if len(punches) == 0:
            for detail in details:
                if detail.datetime_start > now:
                    continue

                values = {
                    "employee_id": employee.id,
                    "check_in": detail.datetime_start,
                    "autopunch": True,
                    "schedule_shift_id": detail.id,
                }
                if detail.datetime_end <= now:
                    values.update({"check_out": detail.datetime_end})
                res |= HrAttendance.create(values)
        # We have partial or full attendance records
        elif len(punches) > 0:
            for detail in details:
                if detail.datetime_start > now:
                    continue
                # We have a detail who's start time has passed

                found = False
                for punch in punches:
                    if punch.check_in == detail.datetime_start:
                        # We've found a corresponding punch time
                        found = True
                        if not punch.check_out:
                            punch.check_out = detail.datetime_end
                            res |= punch
                            break
                # If we didn't find a matching punch create a new one
                if found is False:
                    values = {
                        "employee_id": employee.id,
                        "check_in": detail.datetime_start,
                        "autopunch": True,
                        "schedule_shift_id": detail.id,
                    }
                    if detail.datetime_end <= now:
                        values.update({"check_out": detail.datetime_end})
                    res |= HrAttendance.create(values)
        return res.sorted(None)

    @api.model
    def _get_calendar_and_start_week(self, resource, calendar):

        # If no calendar is specified use working time (calendar) in following order:
        #     - Team working time
        #     - Resource working time
        #
        start_week = 0
        if calendar is None:
            if resource.schedule_team_id:
                start_week = resource.schedule_team_id.start_week
                calendar = resource.schedule_team_id.resource_calendar_id
            else:
                calendar = resource.calendar_id
        return (calendar, start_week)

    @api.model
    def create_schedule(self, resources, date_start, date_end, calendar=None):

        res = self.env["resource.schedule.shift"]
        for resource in resources:
            res |= self._create_schedule(resource, date_start, date_end, calendar)
        return res

    @api.model
    def _create_schedule(self, resource, date_start, date_end, calendar=None):
        """
        Create schedule (shifts) for resource based on calendar (or calendar_id
        of resource, if not specified) between date_start and date_end.
        """

        if date_start > date_end:
            raise ValidationError(
                _("While creating schedules end date cannot be less than start date.")
            )

        schedule_week = 0
        max_week = 0
        calendar, schedule_week = self._get_calendar_and_start_week(resource, calendar)
        if calendar.attendance_ids:
            max_week = calendar.attendance_ids.sorted("sequence")[-1].week_nbr

        week = 0
        values_list = []
        daysoff = self.get_daysoff(resource, calendar, date_start, date_end)
        delta = timedelta(days=1)
        dTmp = date_start
        while dTmp <= date_end:

            if calendar.two_weeks_calendar:
                scheduled_days = calendar.attendance_ids.filtered(
                    lambda a: a.week_nbr == schedule_week and a.display_type is False
                ).mapped("dayofweek")
            else:
                scheduled_days = calendar.attendance_ids.mapped("dayofweek")

            startFlag = True
            prev_weekday = str(dTmp.weekday())
            for attendance in calendar.attendance_ids.filtered(
                lambda a: a.display_type is False and a.week_nbr == schedule_week
            ):

                # skip ahead to the attendance_id corresponding to the
                # week day of date_start
                if startFlag and int(attendance.dayofweek) < dTmp.weekday():
                    continue
                else:
                    startFlag = False

                # If the week day of the attendance is different than the
                # previous processed record move the date forward one day.
                if attendance.dayofweek != prev_weekday:
                    dTmp += delta

                # If we're past the end date stop any further processing
                if dTmp > date_end:
                    break

                # If this is a day off skip ahead to the next attendance_id
                if attendance.dayofweek in daysoff[week]:
                    continue

                # If the week day is not in attendance_ids move the date
                # forward one day until we hit next scheduled day.
                if str(dTmp.weekday()) not in scheduled_days:
                    break

                dtStart = datetime.combine(dTmp, float_to_time(attendance.hour_from))
                if attendance.span_midnight:
                    dtEnd = datetime.combine(
                        dTmp + timedelta(days=1), float_to_time(attendance.hour_to)
                    )
                else:
                    dtEnd = datetime.combine(dTmp, float_to_time(attendance.hour_to))
                dtStart = self.localize_dt(dtStart, calendar.tz, reverse=True)
                dtEnd = self.localize_dt(dtEnd, calendar.tz, reverse=True)
                values = {
                    "resource_id": resource.id,
                    "calendar_id": calendar.id,
                    "template_id": attendance.template_id.id,
                    "datetime_start": dtStart,
                    "datetime_end": dtEnd,
                    "dayofweek": str(dTmp.weekday()),
                    "day_period": attendance.day_period,
                    "span_midnight": attendance.span_midnight,
                    "autopunch": attendance.autopunch,
                    "sequence": attendance.sequence,
                    "shift_type": attendance.shift_type,
                    "flex_core_from": attendance.flex_core_from,
                    "flex_core_to": attendance.flex_core_to,
                    "flex_scheduled_hrs": attendance.flex_scheduled_hrs,
                    "flex_scheduled_avg": attendance.flex_scheduled_avg,
                    "flex_weekly_hrs": attendance.flex_weekly_hrs,
                }
                values_list.append(values)
                prev_weekday = str(dTmp.weekday())

            dTmp += delta
            if dTmp != date_start and dTmp.weekday() == 0:
                week += 1
                if max_week and schedule_week == max_week:
                    schedule_week = 0
                elif max_week:
                    schedule_week += 1

        return self.create(values_list)

    @api.model
    def creat_mass_schedule(self):

        # Create a two-week schedule beginning from Monday of next week.
        #
        dt = datetime.today()
        days = 7 - dt.weekday()
        dt += relativedelta(days=+days)
        dStart = dt.date()
        dEnd = dStart + relativedelta(weeks=+1, days=-1)

        # Create schedules for each employee in each department
        #
        depts = self.env["hr.department"].search([])
        for dept in depts:
            ee_ids = self.env["hr.employee"].search(
                [("department_id", "=", dept.id)], order="name"
            )
            ee_ids.filtered(
                lambda ee: ee.contract_id and ee.contract_id.resource_calendar_id
            )
            for ee in ee_ids:
                ee.create_schedule(dStart, dEnd)

    def publish(self):

        self.published = True

    def unpublish(self):

        self.published = False
