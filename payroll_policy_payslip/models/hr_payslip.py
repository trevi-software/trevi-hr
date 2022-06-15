# Copyright (C) 2013,2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import _, api, fields, models


class LastXDays:
    """Last X Days
    Keeps track of the days an employee worked/didn't work in the last X days.
    """

    def __init__(self, days=6):
        self.limit = days
        self.arr = []

    def reset(self):
        self.arr = []

    def push(self, worked=False):
        if len(self.arr) == (self.limit + 1):
            self.arr.pop(0)
        self.arr.append(worked)
        return [v for v in self.arr]

    def days_worked(self):
        res = 0
        for d in reversed(self.arr):
            if d is True:
                res += 1
            else:
                break
        return res


class HrPayslip(models.Model):

    _inherit = "hr.payslip"

    def attendance_dict_init(self, contract, dFrom, dTo):

        att_obj = self.env["hr.attendance"]

        res = {}
        att_list = att_obj.punches_list_init(contract, dFrom, dTo)
        res.update({"raw_list": att_list})
        d = dFrom
        while d <= dTo:
            res[d] = att_obj.total_hours_on_day(contract, d, punches_list=att_list)
            d += timedelta(days=1)

        return res

    def attendance_dict_list(self, att_dict):

        return att_dict["raw_list"]

    def attendance_dict_hours_on_day(self, d, attendance_dict):

        return attendance_dict[d]

    @api.model
    def holidays_list_init(self, date_from, date_to):

        return self.env["hr.holidays.public"].get_holidays_list(
            start_dt=date_from, end_dt=date_to
        )

    @api.model
    def holidays_list_contains(self, d, holidays_list):

        res = holidays_list.filtered(lambda x: x.date == d)
        return len(res) > 0

    @api.model
    def get_days_off(self, contract):

        res = {
            "default": [],
        }
        daysofweek = ["0", "1", "2", "3", "4", "5", "6"]
        resource_calendar = contract.resource_calendar_id
        for d in daysofweek:
            if d not in resource_calendar.attendance_ids.mapped("dayofweek"):
                res["default"].append(int(d))
        return res

    @api.model
    def require_day_off(self, lsd, presence_policy):

        work_days = 6
        if presence_policy.work_days_per_week:
            work_days = presence_policy.work_days_per_week

        if lsd.days_worked() >= work_days:
            return True

        return False

    @api.model
    def consecutive_days_worked(self, lsd, presence_policy):

        return lsd.days_worked()

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contracts: Browse record of contracts
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """

        res = super().get_worked_day_lines(contracts, date_from, date_to)

        # Initialize list of public holidays. We only need to calculate it once during
        # the lifetime of this object so does it need to be optimized?
        #
        public_holidays_list = self.holidays_list_init(date_from, date_to)

        nb_of_days = (date_to - date_from).days + 1
        presence_data = None
        absence_data = None
        ot_data = None
        att_obj = self.env["hr.attendance"]
        for contract in contracts:

            # Get default set of rest days for this employee/contract
            contract_days_off = self.get_days_off(contract)

            # Initialize dictionary of hours worked per day
            working_hours_dict = self.attendance_dict_init(contract, date_from, date_to)

            # Multiple Contracts in one period handling
            temp_nb_of_days = nb_of_days
            dTempPeriodFrom = date_from
            if len(contracts.ids) > 0:
                if contract.date_start > date_from:
                    dTempPeriodFrom = contract.date_start
                    temp_nb_of_days -= (contract.date_start - date_from).days
                if contract.date_end and contract.date_end < date_to:
                    temp_nb_of_days -= (date_to - contract.date_end).days

            attendances = {
                "MAX": {
                    "name": _("Maximum Possible Working Hours"),
                    "sequence": 1,
                    "code": "MAX",
                    "number_of_days": 0.0,
                    "number_of_hours": 0.0,
                    "contract_id": contract.id,
                },
            }
            normal_working_hours = 0
            awol_code = False

            # Short-circuit:
            # If the policy for the first day is the same as the one for the
            # last day assume that it will also be the same for the days in
            # between, and reuse the same policy instead of checking for every day.
            #
            data2 = None
            presence_data = self.get_presence_policies(
                contract.policy_group_id, date_from, presence_data
            )
            data2 = self.get_presence_policies(contract.policy_group_id, date_to, data2)
            if (presence_data["policy"] and data2["policy"]) and presence_data[
                "policy"
            ].id == data2["policy"].id:
                presence_data["_reuse"] = True

            data2 = None
            absence_data = self.get_absence_policies(
                contract.policy_group_id, date_from, absence_data
            )
            data2 = self.get_absence_policies(contract.policy_group_id, date_to, data2)
            if (absence_data["policy"] and data2["policy"]) and absence_data[
                "policy"
            ].id == data2["policy"].id:
                absence_data["_reuse"] = True

            data2 = None
            ot_data = self.get_ot_policies(contract.policy_group_id, date_from, ot_data)
            data2 = self.get_ot_policies(contract.policy_group_id, date_to, data2)
            if (ot_data["policy"] and data2["policy"]) and ot_data[
                "policy"
            ].id == data2["policy"].id:
                ot_data["_reuse"] = True

            # Calculate the number of days worked in the last week before the
            # start of this contract. Necessary to calculate Weekly Rest Day OT.
            #
            lsd = LastXDays()
            if len(lsd.arr) == 0:
                d = dTempPeriodFrom - timedelta(days=6)
                while d < dTempPeriodFrom:
                    att_count = att_obj.search_count(
                        [
                            ("employee_id", "=", contract.employee_id.id),
                            ("day", "=", d.strftime("%Y-%m-%d")),
                        ],
                    )
                    if att_count > 0:
                        lsd.push(True)
                    else:
                        lsd.push(False)
                    d += timedelta(days=1)

            for day in range(0, temp_nb_of_days):
                dToday = dTempPeriodFrom + timedelta(days=day)
                rest_days = contract_days_off

                # Get Presence policy data
                #
                presence_data = self.get_presence_policies(
                    contract.policy_group_id, dToday, presence_data
                )
                presence_policy = presence_data["policy"]
                presence_sequence = 50

                for (
                    pcode,
                    pname,
                    ptype,
                    prate,
                    pduration,
                    pacc_id,
                    pacc_code,
                    paccrate,
                    paccmin,
                    paccmax,
                ) in presence_data["codes"]:
                    if attendances.get(pcode, False):
                        continue
                    if ptype == "normal":
                        normal_working_hours += float(pduration) / 60.0
                    attendances[pcode] = {
                        "name": pname,
                        "code": pcode,
                        "sequence": presence_sequence,
                        "number_of_days": 0.0,
                        "number_of_hours": 0.0,
                        "rate": prate,
                        "contract_id": contract.id,
                    }
                    presence_sequence += 1

                    # Create accrual input
                    if pacc_id:
                        if self._insert_accrual(
                            contract.id,
                            attendances,
                            pacc_id,
                            pacc_code,
                            paccrate,
                            paccmin,
                            paccmax,
                            presence_sequence,
                        ):

                            presence_sequence += 1

                # Get Absence data
                #
                absence_data = self.get_absence_policies(
                    contract.policy_group_id, dToday, absence_data
                )
                absence_sequence = 100

                for abcode, abname, abtype, abrate, useawol in absence_data["codes"]:
                    if useawol:
                        awol_code = abcode
                    if abtype == "unpaid":
                        abrate = 0
                    elif abtype == "dock":
                        abrate = -abrate

                    if attendances.get(abcode, False):
                        continue

                    # If the leave has already been added by the parent class, only
                    # modify the rate.
                    #
                    res_dict = False
                    for r in res:
                        if r["code"] == abcode:
                            res_dict = r
                            break

                    if res_dict is not False:
                        res_dict["rate"] = abrate
                    else:
                        attendances[abcode] = {
                            "name": abname,
                            "code": abcode,
                            "sequence": absence_sequence,
                            "number_of_days": 0.0,
                            "number_of_hours": 0.0,
                            "rate": abrate,
                            "contract_id": contract.id,
                        }
                        absence_sequence += 1

                # Get OT data
                #
                ot_data = self.get_ot_policies(
                    contract.policy_group_id, dToday, ot_data
                )
                ot_policy = ot_data["policy"]
                daily_ot = ot_data["daily"]
                ot_sequence = 150

                if ot_policy:
                    for (
                        otcode,
                        otname,
                        _ottype,
                        otrate,
                        otacc_id,
                        otacc_code,
                        otaccrate,
                        otaccmin,
                        otaccmax,
                    ) in ot_data["codes"]:
                        if attendances.get(otcode, False):
                            continue
                        attendances[otcode] = {
                            "name": otname,
                            "code": otcode,
                            "sequence": ot_sequence,
                            "number_of_days": 0.0,
                            "number_of_hours": 0.0,
                            "rate": otrate,
                            "contract_id": contract.id,
                        }
                        ot_sequence += 1

                        # Create accrual input
                        if otacc_id:
                            if self._insert_accrual(
                                contract.id,
                                attendances,
                                otacc_id,
                                otacc_code,
                                otaccrate,
                                otaccmin,
                                otaccmax,
                                ot_sequence,
                            ):

                                ot_sequence += 1

                # Is today a holiday?
                public_holiday = self.holidays_list_contains(
                    dToday, public_holidays_list
                )

                # Actual number of hours worked on the day. Based on attendance records.
                working_hours_on_day = self.attendance_dict_hours_on_day(
                    dToday, working_hours_dict
                )

                push_lsd = True
                if working_hours_on_day:
                    done = False

                    if public_holiday:
                        _hours, push_lsd = self._book_holiday_hours(
                            contract,
                            presence_policy,
                            ot_policy,
                            attendances,
                            dToday,
                            rest_days["default"],
                            lsd,
                            working_hours_on_day,
                        )
                        if _hours == 0:
                            done = True
                        else:
                            working_hours_on_day = _hours
                    elif self.require_day_off(lsd, presence_policy):
                        _hours, push_lsd = self._book_restday_hours(
                            contract,
                            presence_policy,
                            ot_policy,
                            attendances,
                            dToday,
                            rest_days["default"],
                            lsd,
                            working_hours_on_day,
                        )
                        if _hours == 0:
                            done = True
                        else:
                            working_hours_on_day = _hours

                    if not done and daily_ot:

                        # Do the OT between specified times (partial OT) first, so that it
                        # doesn't get double-counted in the regular OT.
                        #
                        partial_hr = 0
                        hours_after_ot = working_hours_on_day
                        for line in ot_policy.line_ids:
                            active_after_hrs = float(line.active_after) / 60.0
                            if (
                                line.type == "daily"
                                and working_hours_on_day > active_after_hrs
                                and line.active_start_time
                            ):
                                partial_hr = att_obj.partial_hours_on_day(
                                    contract,
                                    dToday,
                                    active_after_hrs,
                                    line.active_start_time,
                                    line.active_end_time,
                                    line.tz,
                                    punches_list=self.attendance_dict_list(
                                        working_hours_dict
                                    ),
                                )
                                if (
                                    fields.Float.compare(
                                        partial_hr, 0.0, precision_digits=2
                                    )
                                    == 1
                                ):
                                    attendances[line.code][
                                        "number_of_hours"
                                    ] += partial_hr
                                    attendances[line.code]["number_of_days"] += 1.0
                                    hours_after_ot -= partial_hr
                                    working_hours_on_day -= partial_hr

                                    # Process Accruals
                                    accrued_hours = self._get_accrued_accrual(
                                        partial_hr,
                                        line.accrual_rate,
                                        line.accrual_min,
                                        line.accrual_max,
                                    )
                                    if (
                                        fields.Float.compare(
                                            accrued_hours, 0.0, precision_digits=2
                                        )
                                        == 1
                                    ):
                                        self._add_accrued_hours(
                                            line, attendances, accrued_hours
                                        )

                        for line in ot_policy.line_ids:
                            active_after_hrs = float(line.active_after) / 60.0
                            if (
                                line.type == "daily"
                                and hours_after_ot > active_after_hrs
                                and not line.active_start_time
                            ):
                                attendances[line.code][
                                    "number_of_hours"
                                ] += hours_after_ot - (float(line.active_after) / 60.0)
                                attendances[line.code]["number_of_days"] += 1.0

                                # Process Accruals
                                accrued_hours = self._get_accrued_accrual(
                                    hours_after_ot - (float(line.active_after) / 60.0),
                                    line.accrual_rate,
                                    line.accrual_min,
                                    line.accrual_max,
                                )
                                if (
                                    fields.Float.compare(
                                        accrued_hours, 0.0, precision_digits=2
                                    )
                                    == 1
                                ):
                                    self._add_accrued_hours(
                                        line, attendances, accrued_hours
                                    )

                    if not done:
                        for line in presence_policy.line_ids:
                            if line.type == "normal":
                                normal_hours = self._get_applied_time(
                                    working_hours_on_day,
                                    line.active_after,
                                    line.duration,
                                )
                                attendances[line.code][
                                    "number_of_hours"
                                ] += normal_hours
                                attendances[line.code]["number_of_days"] += (
                                    normal_hours > 0 and 1.0 or 0
                                )

                                # Process Accruals
                                accrued_hours = self._get_accrued_accrual(
                                    normal_hours,
                                    line.accrual_rate,
                                    line.accrual_min,
                                    line.accrual_max,
                                )
                                if (
                                    fields.Float.compare(
                                        accrued_hours, 0.0, precision_digits=2
                                    )
                                    == 1
                                ):
                                    self._add_accrued_hours(
                                        line, attendances, accrued_hours
                                    )

                                done = True

                    if push_lsd:
                        lsd.push(True)

                        # If employee has worked 7 consecutive days reset counter
                        if self.consecutive_days_worked(lsd, presence_policy) == 7:
                            lsd.reset()
                else:
                    lsd.push(False)

                if (
                    awol_code
                    and not public_holiday
                    and dToday.weekday() not in rest_days["default"]
                    and working_hours_on_day < normal_working_hours
                ):
                    hours_diff = normal_working_hours - working_hours_on_day
                    attendances[awol_code]["number_of_days"] += (
                        hours_diff > 0 and 1.0 or 0
                    )
                    attendances[awol_code]["number_of_hours"] += hours_diff

                # Calculate total possible working hours in the month
                if dToday.weekday() not in rest_days["default"]:
                    attendances["MAX"]["number_of_hours"] += normal_working_hours
                    attendances["MAX"]["number_of_days"] += (
                        normal_working_hours > 0 and 1.0 or 0
                    )

            attendances = [value for _key, value in attendances.items()]
            res += attendances

        print(f"Res: \n{res}")
        return res

    def _get_policy(self, policy_group, policy_ids, dDay):
        "Return a policy with an effective date before dDay but greater than all others"

        if not policy_group or not policy_ids:
            return None

        res = None
        for policy in policy_ids:
            if policy.date <= dDay and (res is None or policy.date > res.date):
                res = policy
        return res

    def _get_presence_policy(self, policy_group, dDay):
        """Return a Presence Policy with an effective date before dDay but
        greater than all others"""

        return self._get_policy(policy_group, policy_group.presence_policy_ids, dDay)

    def get_presence_policies(self, policy_group_id, day, data):

        if data is None or not data["_reuse"]:
            data = {
                "policy": None,
                "codes": [],
                "_reuse": False,
            }
        elif data["_reuse"]:
            return data

        policy = self._get_presence_policy(policy_group_id, day)

        data["policy"] = policy
        data["codes"] = policy.get_codes()
        return data

    def _get_absence_policy(self, policy_group, dDay):
        """Return an Absence policy with an effective date before dDay but
        greater than all others"""

        res = self._get_policy(policy_group, policy_group.absence_policy_ids, dDay)
        if res is None:
            res = self.env["hr.policy.absence"]
        return res

    def get_absence_policies(self, policy_group_id, day, data):

        if data is None or not data["_reuse"]:
            data = {
                "policy": None,
                "codes": False,
                "_reuse": False,
            }
        elif data["_reuse"]:
            return data

        absence_policy = self._get_absence_policy(policy_group_id, day)

        data["policy"] = absence_policy
        data["codes"] = absence_policy.get_codes()
        return data

    @api.model
    def _get_ot_policy(self, policy_group, dDay):
        """Return an OT policy with an effective date before dDay but
        greater than all others"""

        res = self._get_policy(policy_group, policy_group.ot_policy_ids, dDay)
        if res is None:
            res = self.env["hr.policy.ot"]
        return res

    @api.model
    def get_ot_policies(self, policy_group_id, day, data):

        if data is None or not data["_reuse"]:
            data = {
                "policy": None,
                "daily": None,
                "restday2": None,
                "restday": None,
                "weekly": None,
                "holiday": None,
                "codes": False,
                "_reuse": False,
            }
        elif data["_reuse"]:
            return data

        ot_policy = self._get_ot_policy(policy_group_id, day)
        data["policy"] = ot_policy
        if not ot_policy:
            return data
        daily_ot = ot_policy and len(ot_policy.daily_codes()) > 0 or None
        restday2_ot = ot_policy and len(ot_policy.restday2_codes()) > 0 or None
        restday_ot = ot_policy and len(ot_policy.restday_codes()) > 0 or None
        weekly_ot = ot_policy and len(ot_policy.weekly_codes()) > 0 or None
        holiday_ot = ot_policy and len(ot_policy.holiday_codes()) > 0 or None

        data["codes"] = ot_policy.get_codes()
        data["daily"] = daily_ot
        data["restday2"] = restday2_ot
        data["restday"] = restday_ot
        data["weekly"] = weekly_ot
        data["holiday"] = holiday_ot
        return data

    @api.model
    def _insert_accrual(
        self,
        contract_id,
        attendances,
        accrual_policy_line_id,
        accrual_code,
        rate,
        _ratemin,
        _ratemax,
        sequence,
    ):

        if accrual_code not in attendances:
            attendances[accrual_code] = {
                "name": "Accrual Policy",
                "code": accrual_code,
                "sequence": sequence,
                "number_of_days": 0.0,
                "number_of_hours": 0.0,
                "rate": rate,
                "accrual_policy_line_id": accrual_policy_line_id,
                "contract_id": contract_id,
            }
            return True

        return False

    @api.model
    def _get_accrued_accrual(
        self, worked_hours, pol_acc_rate, pol_acc_min, pol_acc_max
    ):

        acc_precision = 2
        accrued = worked_hours * pol_acc_rate
        if fields.Float.is_zero(accrued, precision_digits=acc_precision):
            return 0

        if (
            not fields.Float.is_zero(pol_acc_min, precision_digits=acc_precision)
            and accrued < pol_acc_min
        ):
            accrued = pol_acc_min
        elif (
            not fields.Float.is_zero(pol_acc_max, precision_digits=acc_precision)
            and accrued > pol_acc_max
        ):
            accrued = pol_acc_max

        return accrued

    @api.model
    def _add_accrued_hours(self, policy_line, attendances, hours):

        attendances[policy_line.accrual_policy_line_id.code]["number_of_hours"] += hours

    @api.model
    def _get_applied_time(self, worked_hours, pol_active_after, pol_duration=False):
        """Returns worked time in hours according to pol_active_after and pol_duration."""

        applied_min = (worked_hours * 60) - pol_active_after
        if fields.Float.compare(applied_min, 0.0, precision_digits=0) == 1:
            applied_min = (
                (pol_duration is not False and applied_min > pol_duration)
                and pol_duration
                or applied_min
            )
        else:
            applied_min = 0
        applied_hours = float(applied_min) / 60.0
        return applied_hours

    @api.model
    def _book_holiday_hours(
        self,
        _contract,
        presence_policy,
        ot_policy,
        attendances,
        dtDay,
        rest_days,
        lsd,
        worked_hours,
    ):

        touched = False
        push_lsd = False
        hours = worked_hours

        # Process normal working hours
        for line in presence_policy.line_ids:
            if line.type == "holiday":
                holiday_hours = self._get_applied_time(
                    worked_hours, line.active_after, line.duration
                )
                attendances[line.code]["number_of_hours"] += holiday_hours
                attendances[line.code]["number_of_days"] += (
                    holiday_hours > 0 and 1.0 or 0
                )

                # Process Accruals
                accrued_hours = self._get_accrued_accrual(
                    holiday_hours, line.accrual_rate, line.accrual_min, line.accrual_max
                )
                if fields.Float.compare(accrued_hours, 0.0, precision_digits=2) == 1:
                    self._add_accrued_hours(line, attendances, accrued_hours)

                hours -= holiday_hours
                touched = True

        # Process OT hours
        for line in ot_policy.line_ids:
            if line.type == "holiday":
                ot_hours = self._get_applied_time(worked_hours, line.active_after)
                attendances[line.code]["number_of_hours"] += ot_hours
                attendances[line.code]["number_of_days"] += ot_hours > 0 and 1.0 or 0

                # Process Accruals
                accrued_hours = self._get_accrued_accrual(
                    ot_hours, line.accrual_rate, line.accrual_min, line.accrual_max
                )
                if fields.Float.compare(accrued_hours, 0.0, precision_digits=2) == 1:
                    self._add_accrued_hours(line, attendances, accrued_hours)

                hours -= ot_hours
                touched = True

        if touched:
            push_lsd = True

        # make 'nearly zero' values zero
        hours = round(hours, 2)

        return hours, push_lsd

    def _book_restday_hours(
        self,
        contract,
        presence_policy,
        ot_policy,
        attendances,
        dtDay,
        rest_days,
        lsd,
        worked_hours,
    ):

        touched = False
        push_lsd = False
        hours = worked_hours

        # Process normal working hours
        for line in presence_policy.line_ids:
            if line.type == "restday" and self.require_day_off(lsd, presence_policy):
                rd_hours = self._get_applied_time(
                    worked_hours, line.active_after, line.duration
                )
                attendances[line.code]["number_of_hours"] += rd_hours
                attendances[line.code]["number_of_days"] += rd_hours > 0 and 1.0 or 0

                # Process Accruals
                accrued_hours = self._get_accrued_accrual(
                    rd_hours, line.accrual_rate, line.accrual_min, line.accrual_max
                )
                if fields.Float.compare(accrued_hours, 0.0, precision_digits=2) == 1:
                    self._add_accrued_hours(line, attendances, accrued_hours)

                hours -= rd_hours
                touched = True

        # Process OT hours
        for line in ot_policy.line_ids:
            if line.type == "restday" and self.require_day_off(lsd, presence_policy):
                ot_hours = self._get_applied_time(worked_hours, line.active_after)
                attendances[line.code]["number_of_hours"] += ot_hours
                attendances[line.code]["number_of_days"] += ot_hours > 0 and 1.0 or 0

                # Process Accruals
                accrued_hours = self._get_accrued_accrual(
                    ot_hours, line.accrual_rate, line.accrual_min, line.accrual_max
                )
                if fields.Float.compare(accrued_hours, 0.0, precision_digits=2) == 1:
                    self._add_accrued_hours(line, attendances, accrued_hours)

                hours -= ot_hours
                touched = True

        if touched:
            push_lsd = True

        # make 'nearly zero' values zero
        hours = round(hours, 2)

        return hours, push_lsd
