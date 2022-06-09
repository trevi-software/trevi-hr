# Copyright (C) 2013,2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from pytz import timezone, utc

from odoo import _, api, exceptions, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def punches_list_init(self, contract, dFrom, dTo):
        """Returns a list containing, for each attendance in range dFrom - dTo, a
        tuple containing: check_in and check_out time."""

        res = []

        # Convert datetime to tz aware datetime according to tz in pay period schedule,
        # then to UTC, and then to naive datetime for comparison with values in db.
        #
        # Also, includue records 48 hours previous to and 48 hours after the desired
        # dates so that any requests for rollover, sessions, etc can be satisfied
        #
        employee = contract.employee_id
        tz_template = timezone(employee.tz)
        dtFrom = datetime.combine(dFrom, datetime.min.time())
        dtFrom += timedelta(hours=-48)
        dtTo = datetime.combine(dTo, datetime.min.time())
        dtTo += timedelta(hours=+48)
        utcdtFrom = tz_template.localize(dtFrom, is_dst=False).astimezone(utc)
        utcdtTo = tz_template.localize(dtTo, is_dst=False).astimezone(utc)
        utcdtDay = utcdtFrom
        utcdtDayEnd = utcdtTo + timedelta(days=1, seconds=-1)
        ndtDay = utcdtDay.replace(tzinfo=None)
        ndtDayEnd = utcdtDayEnd.replace(tzinfo=None)

        attendances = self.search(
            [
                ("employee_id", "=", employee.id),
                "&",
                ("check_in", ">=", ndtDay),
                ("check_in", "<=", ndtDayEnd),
            ],
            order="check_in",
        )

        for a in attendances:
            res.append((a.check_in, a.check_out))

        print(f"punches_list_init returns: {res}")
        return res

    @api.model
    def punches_list_search(self, ndtFrom, ndtTo, punches_list):

        res = []
        for check_in, check_out in punches_list:
            if (
                check_in >= ndtFrom
                and check_in <= ndtTo
                and check_out is False
                or (check_out >= ndtFrom and check_out <= ndtTo)
            ):
                res.append((check_in, check_out))
        return res

    @api.model
    def _calculate_rollover(self, utcdt, rollover_hours):

        # XXX - assume time part of utcdt is already set to midnight
        return utcdt + timedelta(hours=int(rollover_hours))

    @api.model
    def _get_ot_rollover_hours(self, contract):
        return 0

    @api.model
    def _get_ot_rollover_gap(self, contract):
        return 0

    @api.model
    def _get_normalized_punches(self, contract, dDay, punches_list):
        """Returns a tuple containing two lists: in punches, and
        corresponding out punches"""

        #
        # We assume that:
        #    - No dangling sign-in or sign-out
        #

        # Convert datetime to tz aware datetime according to tz in pay period schedule,
        # then to UTC, and then to naive datetime for comparison with values in db.
        #
        employee = contract.employee_id
        dt = datetime.combine(dDay, datetime.min.time())
        utcdtDay = timezone(employee.tz).localize(dt, is_dst=False).astimezone(utc)
        utcdtDayEnd = utcdtDay + timedelta(days=1, seconds=-1)
        ndtDay = utcdtDay.replace(tzinfo=None)
        ndtDayEnd = utcdtDayEnd.replace(tzinfo=None)
        my_list = self.punches_list_search(ndtDay, ndtDayEnd, punches_list)
        if len(my_list) == 0:
            return [], []

        # We are assuming attendances are normalized: (in, out, in, out, ...)
        sin = []
        sout = []
        for check_in, check_out in my_list:
            sin.append(check_in)
            sout.append(check_out)

        if len(sin) == 0 and len(sout) == 0:
            return [], []

        # CHECKS AT THE START OF THE DAY
        # Remove sessions that would have been included in yesterday's attendance.

        # We may have a a session *FROM YESTERDAY* that crossed-over into
        # today. If it is greater than the maximum continuous hours allowed into
        # the next day (as configured in the pay period schedule), then count
        # only the difference between the actual and the maximum continuous
        # hours.
        #
        ot_max_rollover_hours = self._get_ot_rollover_hours(employee)
        ot_max_rollover_gap = self._get_ot_rollover_gap(employee)
        dtRollover = (
            self._calculate_rollover(utcdtDay, ot_max_rollover_hours)
        ).replace(tzinfo=None)
        if (len(sout) - len(sin)) == 0:

            if len(sout) > 0:
                dtSout = sout[0]
                dtSin = sin[0]
                if dtSout > dtRollover and (dtSout < dtSin):
                    sin = [dtRollover] + sin
                elif dtSout < dtSin:
                    sout = sout[1:]
                    # There may be another session that starts within the rollover period
                    if (
                        dtSin < dtRollover
                        and float((dtSin - dtSout).seconds) / 60.0
                        >= ot_max_rollover_gap
                    ):
                        sin = sin[1:]
                        sout = sout[1:]
            else:
                return [], []
        elif (len(sout) - len(sin)) == 1:
            dtSout = sout[0]
            if dtSout > dtRollover:
                sin = [dtRollover] + sin
            else:
                sout = sout[1:]
                # There may be another session that starts within the rollover period
                dtSin = False
                if len(sin) > 0:
                    dtSin = sin[0]
                if (
                    dtSin
                    and dtSin < dtRollover
                    and float((dtSin - dtSout).seconds) / 60.0 >= ot_max_rollover_gap
                ):
                    sin = sin[1:]
                    sout = sout[1:]

        # If the first sign-in was within the rollover gap *AT* midnight check to
        # see if there are any sessions within the rollover gap before it.
        #
        if len(sout) > 0:
            ndtSin = sin[0]
            if (ndtSin - timedelta(minutes=ot_max_rollover_gap)) <= ndtDay:
                my_list4 = self.punches_list_search(
                    ndtDay + timedelta(hours=-24),
                    ndtDay + timedelta(seconds=-1),
                    punches_list,
                )
                if len(my_list4) > 0 and (my_list4[-1][1] is not False):
                    ndtSout = my_list4[-1][0]
                    if ndtSin <= ndtSout + timedelta(minutes=ot_max_rollover_gap):
                        sin = sin[1:]
                        sout = sout[1:]

        # CHECKS AT THE END OF THE DAY
        # Include sessions from tomorrow that should be included in today's attendance.

        # We may have a session that crosses the midnight boundary. If so, add it to today's
        # session.
        #
        dtRollover = (
            self._calculate_rollover(ndtDay + timedelta(days=1), ot_max_rollover_hours)
        ).replace(tzinfo=None)
        if (len(sin) - len(sout)) == 1:

            my_list2 = self.punches_list_search(
                ndtDayEnd + timedelta(seconds=+1),
                ndtDayEnd + timedelta(days=1),
                punches_list,
            )
            if len(my_list2) == 0:
                raise exceptions.ValidationError(
                    _("Attendance Error!"),
                    _("There is not a final sign-out record for %s on %s")
                    % (employee.name, dDay),
                )

            check_in, check_out = my_list2[0]
            if check_out is not False:
                dtSout = check_out
                if dtSout > dtRollover:
                    sout.append(dtRollover)
                else:
                    sout.append(check_out)
                    # There may be another session within the OT max. rollover gap
                    if len(my_list2) > 1:
                        dtSin = check_in
                        if float((dtSin - dtSout).seconds) / 60.0 < ot_max_rollover_gap:
                            sin.append(my_list2[1][0])
                            sout.append(my_list2[1][1])

            else:
                raise exceptions.ValidationError(
                    _("Attendance Error!"),
                    _("There is a sign-in with no corresponding sign-out for %s on %s")
                    % (employee.name, dDay),
                )

        # If the last sign-out was within the rollover gap *BEFORE* midnight check to
        # see if there are any sessions within the rollover gap after it.
        #
        if len(sout) > 0:
            ndtSout = sout[-1]
            if (ndtDayEnd - timedelta(minutes=ot_max_rollover_gap)) <= ndtSout:
                my_list3 = self.punches_list_search(
                    ndtDayEnd + timedelta(seconds=+1),
                    ndtDayEnd + timedelta(hours=+24),
                    punches_list,
                )
                if len(my_list3) > 0:
                    check_in, check_out = my_list3[0]
                    ndtSin = check_in
                    if ndtSin <= ndtSout + timedelta(minutes=ot_max_rollover_gap):
                        sin.append(check_in)
                        sout.append(check_out)

        print(f"_get_normalized_punches returns:\nsin: {sin}\nsout:{sout}")
        return sin, sout

    def _on_day(self, contract, dDay, punches_list=None):
        """Return two lists: the first is sign-in times, and the second is
        corresponding sign-outs."""

        if punches_list is None:
            punches_list = self.punches_list_init(contract, dDay, dDay)

        sin, sout = self._get_normalized_punches(contract, dDay, punches_list)
        if len(sin) != len(sout):
            raise exceptions.ValidationError(
                _("Number of Sign-in and Sign-out records do not match!"),
                _("Employee: %s\nSign-in(s): %s\nSign-out(s): %s")
                % (contract.employee_id.name, sin, sout),
            )

        return sin, sout

    def total_hours_on_day(self, contract, dDay, punches_list=None):
        """Calculate the number of hours worked on specified date."""

        sin, sout = self._on_day(contract, dDay, punches_list=punches_list)

        worked_hours = 0
        for i in range(0, len(sin)):
            start = sin[i]
            end = sout[i]
            worked_hours += float((end - start).seconds) / 60.0 / 60.0

        print(f"total_hours_on_day returns: {worked_hours}")
        return worked_hours
