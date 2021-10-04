# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from pytz import common_timezones, timezone, utc

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT


class Lock(models.Model):

    _name = "base.lock"
    _description = "Base Lock Object"
    _check_company_auto = True

    @api.model
    def _tz_list(self):

        res = tuple()
        for name in common_timezones:
            res += ((name, name),)
        return res

    name = fields.Char(required=True)
    start_time = fields.Datetime(required=True)
    end_time = fields.Datetime(required=True)
    tz = fields.Selection(selection=_tz_list, string="Time Zone", required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        index=True,
        default=lambda self: self.env.company,
        required=True,
    )

    @api.model
    def create(self, vals):
        dt_tz = timezone(vals.get("tz", False))
        dtStart = vals.get("start_time", False)
        dtEnd = vals.get("end_time", False)
        tzStart = dt_tz.localize(dtStart, is_dst=False)
        tzEnd = dt_tz.localize(dtEnd, is_dst=False)
        dtStart = tzStart.astimezone(utc).replace(tzinfo=None)
        dtEnd = tzEnd.astimezone(utc).replace(tzinfo=None)
        vals["start_time"] = dtStart
        vals["end_time"] = dtEnd

        return super(Lock, self).create(vals)

    @api.model
    def is_locked_datetime_utc(self, dt_str):
        """Determines whether a DateTime (string) value falls within a locked period.
        The DateTime string is assumed to be a naive UTC (straight from DB)."""

        lock_ids = self.search(
            ["&", ("start_time", "<=", dt_str), ("end_time", ">=", dt_str)]
        )
        if len(lock_ids) > 0:
            return True

        return False

    @api.model
    def is_locked_date(self, d_str, tz_str=None):
        """Determine if the date (string) is locked. If a time zone is
        specified it will check for midnight according to it, otherwise,
        it is assumed to be UTC"""

        dt_str = d_str + " 00:00:00"
        if tz_str:
            dt_tz = timezone(tz_str)
            dt = datetime.strptime(dt_str, OE_DTFORMAT)
            tzdt = dt_tz.localize(dt, is_dst=False)
            utcdt = tzdt.astimezone(utc)
            dt_str = utcdt.strftime(OE_DTFORMAT)

        return self.is_locked_datetime_utc(dt_str)
