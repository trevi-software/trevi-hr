# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_contract_periods(self):
        """Return the employee's contract periods in chronological order.

        Since Odoo 19 a contract is an ``hr.version`` record, and a single
        contract is described by several versions: a wage revision, for
        instance, creates a new version that keeps the contract dates (see
        ``hr.employee.create_version``). The distinct
        ``(contract_date_start, contract_date_end)`` periods are therefore
        returned, so that a contract is never counted twice. An open-ended
        contract is returned with ``False`` as end date.
        """

        self.ensure_one()
        return sorted(
            {
                (version.contract_date_start, version.contract_date_end)
                for version in self.version_ids
                if version.contract_date_start
            },
            key=lambda period: (period[0], period[1] or date.max),
        )

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
            dToday = date.today()  # noqa: DTZ011
        elif isinstance(dToday, datetime):
            dToday = dToday.date()

        delta = relativedelta(dToday, dToday)
        contracts = self._get_contract_periods()
        if len(contracts) == 0:
            return 0.0

        for dStart, dEnd in contracts:
            if dStart >= dToday:
                continue

            # If the contract doesn't have an end date, use today's date
            # If the contract has finished consider the entire duration of
            # the contract, otherwise consider only the months in the
            # contract until today.
            #
            dEnd = min(dEnd or dToday, dToday)

            delta += relativedelta(dEnd, dStart)

        # Set the number of months the employee has worked
        date_part = float(delta.days) / float(self._get_days_in_month(dToday))
        return round(float((delta.years * 12) + delta.months) + date_part, 2)

    def _compute_employed_months(self):
        for ee in self:
            ee.length_of_service = ee.get_months_service_to_date()

    length_of_service = fields.Float(
        compute="_compute_employed_months", groups=False, string="Seniority"
    )

    def get_employment_date(self):
        self.ensure_one()

        contracts = self._get_contract_periods()
        if len(contracts) > 0:
            return contracts[0][0]

        return None
