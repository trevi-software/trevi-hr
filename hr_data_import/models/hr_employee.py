# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    hire_date = fields.Date(
        help="Initial date of employment if different than date on first contract."
    )
    import_data_id = fields.Many2one("hr.data.import.employee", "Imported Record")

    def get_months_service_to_date(self, dToday=None):
        months = super().get_months_service_to_date(dToday)
        if self.hire_date and self.hire_date < self.first_contract_date:
            if dToday is None:
                dToday = fields.Date.today()
            delta = relativedelta(self.first_contract_date, self.hire_date)
            months += round(
                float(
                    delta.years * 12
                    + delta.months
                    + delta.days / float(self._get_days_in_month(dToday))
                ),
                2,
            )
        return months
