##############################################################################
#
#    Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    def _get_contracts_list(self):
        """Return list of contracts in chronological order"""

        self.ensure_one()
        contracts = self.env["hr.contract"]
        if len(self.contract_ids) > 0:
            contracts = self.contract_id.sorted(key=lambda c: c.date_start)

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
        """Returns a dictionary of floats. The key is the employee id, and the value is
        number of months of employment."""

        self.ensure_one()
        if dToday is None:
            dToday = date.today()
        elif isinstance(dToday, datetime):
            dToday = dToday.date()

        delta = relativedelta(dToday, dToday)
        contracts = self._get_contracts_list()
        if len(contracts) == 0:
            return (0.0, False)

        dInitial = datetime.strptime(contracts[0].date_start, OE_DATEFORMAT).date()

        for c in contracts:
            dStart = datetime.strptime(c.date_start, "%Y-%m-%d").date()
            if dStart >= dToday:
                continue

            # If the contract doesn't have an end date, use today's date
            # If the contract has finished consider the entire duration of
            # the contract, otherwise consider only the months in the
            # contract until today.
            #
            if c.date_end:
                dEnd = datetime.strptime(c.date_end, "%Y-%m-%d").date()
            else:
                dEnd = dToday
            if dEnd > dToday:
                dEnd = dToday

            delta += relativedelta(dEnd, dStart)

        # Set the number of months the employee has worked
        date_part = float(delta.days) / float(self._get_days_in_month(dInitial))
        return (
            round(float((delta.years * 12) + delta.months) + date_part, 2),
            dInitial,
        )

    def _compute_employed_months(self):

        for ee in self:
            ee.length_of_service = ee.get_months_service_to_date()[0]

    length_of_service = fields.Float(compute="_compute_employed_months", groups=False)

    def get_employment_date(self):

        self.ensure_one()

        dFirstcontract = None
        contracts = self._get_contracts_list()
        if len(contracts) > 0:
            dFirstcontract = datetime.strptime(
                contracts[0].date_start, OE_DATEFORMAT
            ).date()

        return dFirstcontract
