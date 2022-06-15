# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from pytz import timezone, utc

from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    day = fields.Date(compute="_compute_day", store=True)

    @api.depends("check_in")
    def _compute_day(self):

        for att in self:
            local_tz = timezone(att.employee_id.tz)
            utc_check_in = utc.localize(att.check_in)
            tz_check_in = utc_check_in.astimezone(local_tz)
            att.day = tz_check_in.date()
