# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    def _get_contracts_list(self):
        """Return list of contracts in chronological order"""

        self.ensure_one()
        contracts = self.env["hr.contract"]
        if len(self.contract_ids) > 0:
            contracts = self.contract_ids.sorted(key=lambda c: c.date_start)

        return contracts

    def _get_days_in_month(self, d):

        last_date = (
            d
            - timedelta(days=(d.day - 1))
            + relativedelta(months=+1)
            + relativedelta(days=-1)
        )
        return last_date.day

    def get_months_service_to_date(self, dToday=None):
        """Returns the number of months of employment."""

        self.ensure_one()
        if dToday is None:
            dToday = date.today()
        elif isinstance(dToday, datetime):
            dToday = dToday.date()

        delta = relativedelta(dToday, dToday)
        contracts = self._get_contracts_list()
        if len(contracts) == 0:
            return 0.0

        dInitial = fields.Date.to_date(contracts[0].date_start)

        for c in contracts:
            dStart = c.date_start
            if dStart >= dToday:
                continue

            # If the contract doesn't have an end date, use today's date
            # If the contract has finished consider the entire duration of
            # the contract, otherwise consider only the months in the
            # contract until today.
            #
            if c.date_end:
                dEnd = c.date_end
            else:
                dEnd = dToday
            if dEnd > dToday:
                dEnd = dToday

            delta += relativedelta(dEnd, dStart)

        # Set the number of months the employee has worked
        date_part = float(delta.days) / float(self._get_days_in_month(dInitial))
        return round(float((delta.years * 12) + delta.months) + date_part, 2)

    def _compute_employed_months(self):

        for ee in self:
            ee.length_of_service = self.get_months_service_to_date()

    length_of_service = fields.Float(
        compute="_compute_employed_months", groups=False, string="Seniority (months)"
    )

    def get_employment_date(self):

        self.ensure_one()

        contracts = self._get_contracts_list()
        if len(contracts) > 0:
            return contracts[0].date_start

        return None
