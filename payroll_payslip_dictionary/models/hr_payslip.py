# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from calendar import monthrange
from datetime import timedelta

from odoo import SUPERUSER_ID, api, models


# Used to allow nested dicts to be accessed with '.' (dot) notation
class BasicBrowsableObject(object):
    def __init__(self, vals_dict):
        self.values = vals_dict

    def __getattr__(self, attr):
        return attr in self.values and self.values.__getitem__(attr) or 0.0

    def __setattr__(self, attr, value):
        if attr == "values":
            return super().__setattr__(attr, value)
        self.__dict__["values"][attr] = value

    def __str__(self):
        return str(self.values)


class HrPayslip(models.Model):

    _inherit = "hr.payslip"

    @api.model
    def _get_working_defaults(self):
        """
        This method returns the default working hours and days.
        @return: returns a tuple containing:
            * regular working hours in a day
            * working hours per week
            * number of working days per month
        """

        IrConfig = self.env["ir.config_parameter"].with_user(SUPERUSER_ID)
        daily_max_regular_hours = int(
            IrConfig.get_param("payroll_payslip_dictionary.daily_max_regular_hours")
        )
        weekly_max_regular_hours = int(
            IrConfig.get_param("payroll_payslip_dictionary.weekly_max_regular_hours")
        )
        monthly_max_working_days = int(
            IrConfig.get_param("payroll_payslip_dictionary.monthly_max_working_days")
        )
        return (
            daily_max_regular_hours,
            weekly_max_regular_hours,
            monthly_max_working_days,
        )

    def _get_working_calendar(self, contract):

        return self._get_working_calendar_from_dates(
            contract, self.date_from, self.date_to
        )

    def _get_working_calendar_from_dates(self, contract, dStart, dEnd):
        """
        This method calculates working hours and days according to dStart and dEnd.
        @return: returns a tuple containing:
            * regular working hours in a day
            * working hours per week
            * number of working days per month
        """

        business_days = []
        weekly_hours = 0
        daily_hours = (
            contract.resource_calendar_id.hours_per_day
            if contract.resource_calendar_id
            else 8
        )
        for att in contract.resource_calendar_id.attendance_ids:
            weekly_hours += abs(att.hour_to - att.hour_from)
            if int(att.dayofweek) not in business_days:
                business_days.append(int(att.dayofweek))

        # XXX - Edge case, please fix if it affects you
        if contract.resource_calendar_id.two_weeks_calendar:
            weekly_hours = weekly_hours / 2

        # generate dates in period
        dates = [dStart + timedelta(idx) for idx in range((dEnd - dStart).days + 1)]
        # sum up the working days
        total_days = sum(1 for day in dates if day.weekday() in business_days)

        return (daily_hours, weekly_hours, total_days)

    def _get_end_date(self, contract):
        """
        @return: returns False or the end date of the contract if it falls before
        the end date of the period or the end date of the period otherwise.
        """

        dcEnd = False
        if contract.date_end:
            if contract.date_end <= self.date_to:
                dcEnd = contract.date_end
            else:
                dcEnd = self.date_to

        return dcEnd

    def _ppf_get_contract_max_days(
        self,
        contract,
        wd_calculation,
        total_days,
        dContractStart,
        dContractEnd,
        dPeriodStart,
        dPeriodEnd,
    ):
        """
        @return: returns a tuple containing:
            * the maximum possible working days in this contract
            * the maximum possible working days for other contracts in this period
        """

        if wd_calculation == "resource_calendar":
            contract_days = self._get_working_calendar_from_dates(
                contract, dContractStart, dContractEnd
            )[2]
        else:
            period_days = (dPeriodEnd - dPeriodStart).days + 1
            contract_days_ratio = (
                (dContractEnd - dContractStart).days + 1
            ) / period_days
            contract_days = round(total_days * contract_days_ratio)
        other_max_days = total_days - contract_days

        return (contract_days, other_max_days)

    def _partial_payroll_factor(self, contract, contracts):

        self.ensure_one()

        dcEnd = self._get_end_date(contract)

        # both start and end of contract are out of the bounds of the payslip
        if contract.date_start <= self.date_from and (
            not dcEnd or dcEnd >= self.date_to
        ):
            return 1

        # One or both start and end of contract are within the bounds of the payslip
        #
        dcTempStart = self.date_from
        dcTempEnd = self.date_to
        if contract.date_start > self.date_from:
            dcTempStart = contract.date_start
        if dcEnd and dcEnd < self.date_to:
            dcTempEnd = dcEnd

        # Get number of working days in pay period
        #
        IrConfig = self.env["ir.config_parameter"].with_user(SUPERUSER_ID)
        wd_calculation = IrConfig.get_param(
            "payroll_payslip_dictionary.working_days_calculation"
        )
        if wd_calculation == "resource_calendar" and contract.resource_calendar_id:
            total_days = self._get_working_calendar(contract)[2]
        elif wd_calculation == "calendar":
            total_days = monthrange(self.date_from.year, self.date_from.month)[1]
        else:
            total_days = self._get_working_defaults()[2]

        # Get maximum number of working days in the contract
        contract_days, other_days = self._ppf_get_contract_max_days(
            contract,
            wd_calculation,
            total_days,
            dcTempStart,
            dcTempEnd,
            self.date_from,
            self.date_to,
        )
        contracts_total = contract_days + other_days

        # Adjust total days in month based on actual work days. This might
        # differ from total_days calculated above if, for example, the maximum
        # working days in multiple contracts add up less than the defaults.
        #
        if len(contracts) > 1 and contracts_total < total_days:
            total_days = contracts_total

        # Adjust the contract days to the calculation that gives the most days
        # within the bounds of the total possible days.
        #
        if contract_days > total_days:
            contract_days = total_days

        return float(contract_days) / float(total_days)

    def get_dictionary(self, contracts):
        """
        @return: returns a dictionary containing:
            * max_weekly_hours  - the number of weekly working hours
            * max_working_days  - the number of working days in the period
            * max_working_hours - the number of working hours in the period
            * seniority - the number of months of employment
            * PREVPS
                exists  - 0 or 1 if the employee had a payslip in the previous period
                net     - 0 or Net amount received by employee in previous period
            * CONTRACTS
                qty     - the number of contracts for this employee in this period
                cummulative_ppf - sum of PPF of the employee's contracts in this
                                  period
        """

        self.ensure_one()
        res = {
            "max_weekly_hours": 0,
            "max_working_days": 0,
            "max_working_hours": 0,
            "seniority": 0,
            "PREVPS": BasicBrowsableObject(
                {
                    "exists": 0,
                    "net": 0,
                }
            ),
            "CONTRACTS": BasicBrowsableObject(
                {
                    "qty": 0,
                    "cummulative_ppf": 0,
                }
            ),
        }

        # Calculate maximum values
        max_weekly_hours = 0
        max_working_days = 0
        IrConfig = self.env["ir.config_parameter"].with_user(SUPERUSER_ID)
        wd_calculation = IrConfig.get_param(
            "payroll_payslip_dictionary.working_days_calculation"
        )
        contract = contracts[0]
        if wd_calculation == "resource_calendar" and contract.resource_calendar_id:
            daily_hrs, max_weekly_hours, max_working_days = self._get_working_calendar(
                contract
            )
        elif wd_calculation == "calendar":
            daily_hrs, max_weekly_hours, max_working_days = self._get_working_defaults()
            max_working_days = monthrange(self.date_from.year, self.date_from.month)[1]
        else:
            daily_hrs, max_weekly_hours, max_working_days = self._get_working_defaults()
        res["max_weekly_hours"] = max_weekly_hours
        res["max_working_days"] = max_working_days
        res["max_working_hours"] = max_working_days * daily_hrs

        # Calculate seniority
        if self.employee_id:
            res["seniority"] = self.employee_id.get_months_service_to_date(self.date_to)

        # Calculate net amount of previous payslip
        ps_ids = self.env["hr.payslip"].search(
            [("employee_id", "=", self.employee_id.id), ("state", "=", "done")],
            order="date_from desc",
            limit=1,
        )

        if len(ps_ids) > 0:
            # Get payroll code of Net salary rule
            code_net = IrConfig.get_param("payroll_payslip_dictionary.payroll_code_net")

            ps = ps_ids[0]
            res["PREVPS"].exists = 1
            total = 0
            for line in ps.line_ids:
                if line.salary_rule_id.code == code_net:
                    total += line.total
            res["PREVPS"].net = total

        ppf_total = 0
        for c in contracts:
            ppf_total += self._partial_payroll_factor(c, contracts)
        res["CONTRACTS"].qty = len(contracts.ids)
        res["CONTRACTS"].cummulative_ppf = ppf_total > 1 and 1 or ppf_total

        return res

    def get_contract_dictionary(self, contract, contracts):
        """
        @return: returns a dictionary containing:
            * ppf - payroll period factor: the percentage of the pay period
                    for the contract. A value of 1 means the contract covers
                    the entire payslip period.
            * hourly_wage - the wage on the contract converted to an hourly rate
            * daily_wage  - the wage on the contract converted to a daily rate
        """

        self.ensure_one()
        IrConfig = self.env["ir.config_parameter"].with_user(SUPERUSER_ID)
        res = {"ppf": 0, "hourly_wage": 0.0, "daily_wage": 0.0}

        # Calculate percentage of pay period in which contract lies
        if contract:
            payroll_decimal_places = 2
            decimal_places = 4
            payroll_ref = self.with_user(SUPERUSER_ID).env.ref(
                "payroll.decimal_payroll"
            )
            if payroll_ref:
                payroll_decimal_places = payroll_ref.digits
            payroll_rate_ref = self.with_user(SUPERUSER_ID).env.ref(
                "payroll.decimal_payroll_rate"
            )
            if payroll_rate_ref:
                decimal_places = payroll_rate_ref.digits
            res["ppf"] = round(
                self._partial_payroll_factor(contract, contracts),
                decimal_places,
            )

            # Calculate hourly and daily rates
            daily_hrs = 0
            total_days = 0
            wd_calculation = IrConfig.get_param(
                "payroll_payslip_dictionary.working_days_calculation"
            )
            if wd_calculation == "resource_calendar" and contract.resource_calendar_id:
                daily_hrs, _weekly_hrs, total_days = self._get_working_calendar(
                    contract
                )
            elif wd_calculation == "calendar":
                daily_hrs, _weekly_hrs, total_days = self._get_working_defaults()
                total_days = monthrange(self.date_from.year, self.date_from.month)[1]
            else:
                daily_hrs, _weekly_hrs, total_days = self._get_working_defaults()
            res["daily_wage"] = round(
                contract.wage / total_days, payroll_decimal_places
            )
            res["hourly_wage"] = round(
                contract.wage / total_days / daily_hrs, payroll_decimal_places
            )

        return res

    def get_localdict(self, contracts):

        res = super().get_localdict(contracts)
        res.update(self.get_dictionary(contracts))
        return res

    def get_contractdict(self, contract, contracts):

        res = super().get_contractdict(contract, contracts)
        res.update(self.get_contract_dictionary(contract, contracts))
        return res
