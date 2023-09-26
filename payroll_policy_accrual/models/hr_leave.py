# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrHolidays(models.Model):

    _inherit = "hr.leave.allocation"

    def do_accrual(self, today, days):

        self.ensure_one()
        Accrual = self.env["hr.accrual"]
        AccrualLine = self.env["hr.accrual.line"]

        accrual_ids = Accrual.search(
            [("holiday_status_id", "=", self.holiday_status_id.id)]
        )

        if len(accrual_ids) == 0:
            return

        # Deposit to the accrual account
        #
        accrual_line = {
            "date": today,
            "accrual_id": accrual_ids[0],
            "employee_id": self.employee_id.id,
            "amount": days,
        }
        line_id = AccrualLine.create(accrual_line)
        accrual_ids[0].write({"line_ids": [(4, line_id)]})

        return

    def action_validate(self):

        res = super(HrHolidays, self).action_validate()

        today = fields.Date.today()
        for record in self:
            if record.holiday_type == "employee" and record.from_accrual:

                record._do_accrual(
                    today, record.employee_id.id, record.number_of_days_temp
                )

            if record.holiday_type == "employee":

                record._do_accrual(
                    today, record.employee_id.id, -record.number_of_days_temp
                )

        return res

    def holidays_refuse(self):

        today = fields.Date.today()
        for record in self:
            if record.state not in ["validate", "validate1"]:
                continue

            if record.holiday_type == "employee" and record.type == "add":
                self._do_accrual(
                    today,
                    record.holiday_status_id.id,
                    record.employee_id.id,
                    -record.number_of_days_temp,
                )

            elif record.holiday_type == "employee" and record.type == "remove":
                self._do_accrual(
                    today,
                    record.holiday_status_id.id,
                    record.employee_id.id,
                    record.number_of_days_temp,
                )

        return super(HrHolidays, self).holidays_refuse()
