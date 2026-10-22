# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from pytz import timezone, utc

from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    day = fields.Date(compute="_compute_day", store=True)

    # the compute reads employee_id.tz, so it must depend on it as well: for a
    # 21:00 UTC check-in the day differs between Accra (UTC+0) and Addis (UTC+3)
    @api.depends("check_in", "employee_id.tz")
    def _compute_day(self):
        for att in self:
            # the field can be empty while the user is editing the form, and the
            # compute runs before anything is saved
            if not att.check_in:
                att.day = False
                continue
            local_tz = timezone(att.employee_id.tz or "UTC")
            utc_check_in = utc.localize(att.check_in)
            tz_check_in = utc_check_in.astimezone(local_tz)
            att.day = tz_check_in.date()
