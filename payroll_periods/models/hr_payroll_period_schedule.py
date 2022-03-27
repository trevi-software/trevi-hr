# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import calendar
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from pytz import common_timezones, timezone, utc

from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT


# http://stackoverflow.com/questions/4130922/how-to-increment-datetime-month-in-python
#
def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def get_period_year(dt, annual_pay_periods):

    month_number = 0
    year_number = 0
    if dt.day < 15:
        month_name = dt.strftime("%B")
        month_number = dt.month
        year_number = dt.year
    else:
        dtTmp = add_months(dt, 1)
        if annual_pay_periods > 12:
            # Maybe bi-weekly?
            month_name = dt.strftime("%B")
        else:
            month_name = dtTmp.strftime("%B")
        month_number = dtTmp.month
        year_number = dtTmp.year
    return month_name, month_number, year_number


class HrPayperiodSchedule(models.Model):

    _name = "hr.payroll.period.schedule"
    _description = "Payroll Period Schedule"
    _check_company_auto = True

    @api.model
    def _tz_list(self):

        res = tuple()
        for name in common_timezones:
            res += ((name, name),)
        return res

    def _compute_annual_periods(self):

        for pps in self:
            if pps.type == "manual":
                pps.annual_pay_periods = 0
            elif pps.type == "monthly":
                pps.annual_pay_periods = 12

    name = fields.Char(string="Description", required=True)
    tz = fields.Selection(selection=_tz_list, string="Time Zone", required=True)
    paydate_biz_day = fields.Boolean(string="Pay Date on a Business Day")
    ot_week_startday = fields.Selection(
        string="Start of Week",
        selection=[
            ("0", _("Sunday")),
            ("1", _("Monday")),
            ("2", _("Tuesday")),
            ("3", _("Wednesday")),
            ("4", _("Thursday")),
            ("5", _("Friday")),
            ("6", _("Saturday")),
        ],
        default="1",
        required=True,
    )
    ot_max_rollover_hours = fields.Integer(
        string="OT Max. Continous Hours", required=True, default=6
    )
    ot_max_rollover_gap = fields.Integer(
        string="OT Max. Continuous Hours Gap (in Min.)", required=True, default=60
    )
    type = fields.Selection(
        selection=[
            ("manual", "Manual"),
            ("monthly", "Monthly"),
        ],
        required=True,
        default="monthly",
    )
    annual_pay_periods = fields.Integer(compute=_compute_annual_periods)
    mo_firstday = fields.Selection(
        string="Start Day",
        selection=[
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
            ("14", "14"),
            ("15", "15"),
            ("16", "16"),
            ("17", "17"),
            ("18", "18"),
            ("19", "19"),
            ("20", "20"),
            ("21", "21"),
            ("22", "22"),
            ("23", "23"),
            ("24", "24"),
            ("25", "25"),
            ("26", "26"),
            ("27", "27"),
            ("28", "28"),
            ("29", "29"),
            ("30", "30"),
            ("31", "31"),
        ],
        default="1",
    )
    mo_paydate = fields.Selection(
        string="Pay Date",
        selection=[
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
            ("14", "14"),
            ("15", "15"),
            ("16", "16"),
            ("17", "17"),
            ("18", "18"),
            ("19", "19"),
            ("20", "20"),
            ("21", "21"),
            ("22", "22"),
            ("23", "23"),
            ("24", "24"),
            ("25", "25"),
            ("26", "26"),
            ("27", "27"),
            ("28", "28"),
            ("29", "29"),
            ("30", "30"),
            ("31", "31"),
        ],
        default="3",
    )
    contract_ids = fields.One2many(
        string="Contracts", comodel_name="hr.contract", inverse_name="pps_id"
    )
    pay_period_ids = fields.One2many(
        string="Pay Periods",
        comodel_name="hr.payroll.period",
        inverse_name="schedule_id",
        check_company=True,
    )
    initial_period_date = fields.Date(string="Initial Period Start Date", required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    def button_add_pay_periods(self):

        for sched in self:
            sched.add_pay_period()

    def add_pay_period(self):

        #
        # XXX - Someone who cares about DST should update this code to handle it.
        #

        self.ensure_one()
        data = None
        latest = self._get_latest_period(self.id)
        local_tz = timezone(self.tz)
        if not latest:
            # No pay periods have been defined yet for this pay period schedule.
            if self.type == "monthly":
                dtStart = False
                dStart = self.initial_period_date
                if dStart.day > int(self.mo_firstday):
                    dStart = add_months(dStart, 1)
                    dtStart = datetime(
                        dStart.year, dStart.month, int(self.mo_firstday), 0, 0, 0
                    )
                elif dStart.day < int(self.mo_firstday):
                    dtStart = datetime(
                        dStart.year, dStart.month, int(self.mo_firstday), 0, 0, 0
                    )
                else:
                    dtStart = datetime(dStart.year, dStart.month, dStart.day, 0, 0, 0)
                dtEnd = add_months(dtStart, 1) - timedelta(days=1)
                dtEnd = datetime(dtEnd.year, dtEnd.month, dtEnd.day, 23, 59, 59)
                month_name, _month_number, year_number = get_period_year(dtStart, 12)

                # Convert from time zone of punches to UTC for storage
                ltzStart = local_tz.localize(dtStart, is_dst=None)
                utcStart = ltzStart.astimezone(utc)
                ltzEnd = local_tz.localize(dtEnd, is_dst=None)
                utcEnd = ltzEnd.astimezone(utc)
                dtStart = utcStart.replace(tzinfo=None)
                dtEnd = utcEnd.replace(tzinfo=None)

                data = {
                    "name": _("Pay Period {}/{}").format(
                        str(year_number), str(month_name)
                    ),
                    "schedule_id": self.id,
                    "date_start": dtStart,
                    "date_end": dtEnd,
                }
        else:
            if self.type == "monthly":
                # Convert from UTC to timezone of punches
                dtStart = latest.date_end
                utcStart = utc.localize(dtStart, is_dst=None)
                utcStart += timedelta(seconds=1)
                ltzStart = utcStart.astimezone(local_tz)

                # Roll forward to the next pay period start and end times
                dEnd = add_months(ltzStart.replace(tzinfo=None), 1) - timedelta(days=1)
                ltzEnd = local_tz.localize(
                    datetime(dEnd.year, dEnd.month, dEnd.day, 23, 59, 59)
                )
                month_name, _month_number, year_number = get_period_year(ltzStart, 12)

                # Convert from time zone of punches to UTC for storage
                utcStart = ltzStart.astimezone(utc)
                utcEnd = ltzEnd.astimezone(utc)
                dtStart = utcStart.replace(tzinfo=None)
                dtEnd = utcEnd.replace(tzinfo=None)

                data = {
                    "name": _("Pay Period {}/{}").format(
                        str(year_number), str(month_name)
                    ),
                    "schedule_id": self.id,
                    "date_start": dtStart,
                    "date_end": dtEnd,
                }

        # Run hook method to give other modules a chance to edit the data
        if data is None:
            data = {}
        data.update(self.payroll_period_data_hook(data))
        self.write({"pay_period_ids": [(0, 0, data)]})

    @api.model
    def payroll_period_data_hook(self, _data=None):

        return {}

    @api.model
    def _get_latest_period(self, sched_id):

        PayrollPeriod = self.env["hr.payroll.period"]
        srch_domain = [("schedule_id", "=", sched_id)]

        pp_ids = PayrollPeriod.search(srch_domain)
        latest_period = False
        for period in pp_ids:
            if not latest_period:
                latest_period = period
                continue
            if period.date_end > latest_period.date_end:
                latest_period = period

        return latest_period

    @api.model
    def try_create_new_period(self):
        """Try and create pay periods for up to 3 months from now."""

        #
        # XXX - Someone who cares about DST should update this code to handle it.
        #

        dtNow = datetime.now()
        dtNow = datetime.strptime(dtNow.strftime("%Y-%m-1 00:00:00"), OE_DTFORMAT)
        sched_ids = self.env["hr.payroll.period.schedule"].search([])

        for sched in sched_ids:

            # Add up to three periods from now. If there are not periods in
            # the database start from the configured initial date.
            #
            latest_period = self._get_latest_period(sched.id)
            loclDTNow = timezone(sched.tz).localize(dtNow, is_dst=False)
            utcDTFuture = loclDTNow.astimezone(utc) + relativedelta(months=2)

            # 53 because we want to support weekly pay periods (52 weeks/year)
            for _i in range(53):
                # Don't go any further than 3 months (including this month)
                latest_period = self._get_latest_period(sched.id)
                if latest_period:
                    utcdtPeriod = utc.localize(latest_period.date_start, is_dst=False)
                    if utcdtPeriod >= utcDTFuture:
                        break
                    sched.add_pay_period()
                else:
                    sched.add_pay_period()
