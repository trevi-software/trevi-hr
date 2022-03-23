# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import api, fields, models


class HrAttendance(models.Model):

    _inherit = "hr.attendance"

    autopunch = fields.Boolean(
        string="Auto-punch",
        help="Designates whether or not this attendance record was created automatically.",
    )
    schedule_shift_id = fields.Many2one(
        "resource.schedule.shift", "Shift", help="The shift related to this attendance."
    )

    @api.model
    def auto_punchout(self):
        now = fields.Datetime.now()
        return self._auto_punchout(now)

    @api.model
    def _auto_punchout(self, now):
        """
        This method automatically clocks out attendance records that have
        exceeded the maximum shift length.
        :param datetime now: the current UTC datetime in naive datetime format.
        :returns: :class:`~hr.attendance`
        """
        res = self.env["hr.attendance"]
        max_shift_length = int(
            self.env["ir.config_parameter"].get_param(
                "resource_schedule.max_shift_length"
            )
        )
        if max_shift_length == 0 or max_shift_length is False:
            return res

        atts = self.search([("check_out", "=", False), ("check_in", "!=", False)])
        atts = atts.filtered(lambda att: att._exceeds_max_duration(now))
        if len(atts) > 0:
            for at in atts:
                at.check_out = at.check_in + timedelta(hours=int(max_shift_length))
            res = atts
        return res

    def _exceeds_max_duration(self, now):

        duration = now - self.check_in
        return int(duration.total_seconds() / 60.0 / 60.0) >= 15
