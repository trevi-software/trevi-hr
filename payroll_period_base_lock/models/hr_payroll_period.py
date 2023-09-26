# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT


class PayrollPeriod(models.Model):
    _inherit = "hr.payroll.period"

    lock_id = fields.Many2one(comodel_name="base.lock", string="Payroll Lock")
    state = fields.Selection(
        selection_add=[
            ("open",),
            ("ended",),
            ("locked", "Locked"),
            ("generate",),
            ("payment",),
            ("closed",),
        ],
    )

    @api.model
    def lock_period(self, periods, employee_ids):

        PayrollLock = self.env["base.lock"]
        for period in periods:
            utcDtStart, utcDtEnd = self.get_utc_times(period)
            lock_id = PayrollLock.create(
                {
                    "name": period.name,
                    "start_time": utcDtStart.strftime(OE_DTFORMAT),
                    "end_time": utcDtEnd.strftime(OE_DTFORMAT),
                    "tz": period.schedule_id.tz,
                }
            )
            period.lock_id = lock_id

        return

    @api.model
    def unlock_period(self, periods, employee_ids):

        for period in periods:
            if period.lock_id:
                period.lock_id.unlink()

        return

    def set_state_locked(self):

        for period in self:
            self.lock_period([period])
            period.state = "locked"

        return True

    @api.model
    def is_payroll_locked(self, utcdt_str):

        PayrollLock = self.env["base.lock"]
        is_locked = PayrollLock.is_locked_datetime_utc(utcdt_str)

        return is_locked
