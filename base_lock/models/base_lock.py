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
        res = ()
        for name in common_timezones:
            res += ((name, name),)
        return res

    name = fields.Char(required=True)
    start_time = fields.Datetime(required=True)
    end_time = fields.Datetime(required=True)
    tz = fields.Selection(selection=_tz_list, string="Time Zone", required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        index=True,
        default=lambda self: self.env.company,
        required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Datetimes arrive as strings from JSON-RPC payloads and from values
            # taken off read(), and the ORM only converts them inside
            # super().create(). pytz's localize() needs datetime objects, so
            # normalise first (to_datetime returns None for False/missing).
            dtStart = fields.Datetime.to_datetime(vals.get("start_time"))
            dtEnd = fields.Datetime.to_datetime(vals.get("end_time"))
            if dtStart and dtEnd and vals.get("tz"):
                dt_tz = timezone(vals["tz"])
                dtStart = dt_tz.localize(dtStart, is_dst=False)
                dtEnd = dt_tz.localize(dtEnd, is_dst=False)
                vals["start_time"] = dtStart.astimezone(utc).replace(tzinfo=None)
                vals["end_time"] = dtEnd.astimezone(utc).replace(tzinfo=None)

        return super().create(vals_list)

    @api.model
    def is_locked_datetime_utc(self, dt_str):
        """Determines whether a DateTime (string) value falls within a locked period.
        The DateTime string is assumed to be a naive UTC (straight from DB).

        Locks are company-scoped: neither ``_check_company_auto`` nor the
        security file restricts the search, so the current company has to be
        filtered explicitly, otherwise a lock owned by one company would lock
        the same period for every other company.
        """

        lock_ids = self.search(
            [
                ("company_id", "=", self.env.company.id),
                ("start_time", "<=", dt_str),
                ("end_time", ">=", dt_str),
            ]
        )

        return len(lock_ids) > 0

    @api.model
    def is_locked_date(self, d_str, tz_str=None):
        """Determine if the date (string) is locked. If a time zone is
        specified it will check for midnight according to it, otherwise,
        it is assumed to be UTC"""

        dt_str = d_str + " 00:00:00"
        if tz_str:
            tz = timezone(tz_str)
            dt_str = (
                tz.localize(datetime.strptime(dt_str, OE_DTFORMAT), is_dst=False)  # noqa: DTZ007
                .astimezone(utc)
                .strftime(OE_DTFORMAT)
            )

        return self.is_locked_datetime_utc(dt_str)
