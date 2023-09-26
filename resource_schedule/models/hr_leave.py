# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import models


class HrLeave(models.Model):

    _inherit = "hr.leave"

    def action_validate(self):

        res = super(HrLeave, self).action_validate()

        lv_requests = self.filtered(lambda lv: lv.holiday_type == "employee")

        Attendance = self.env["hr.attendance"]
        for lv in lv_requests:

            # Adjust shifts around the leave
            dictIds = self.adjust_schedule_by_leave()

            # Adjust attendances
            #
            if len(dictIds["removed_ids"]) > 0:
                att_ids = Attendance.sudo().search(
                    [("id", "in", dictIds["removed_ids"])],
                )
                att_ids.unlink()
            if len(dictIds["in_altered_ids"]) > 0:
                _unlink_ids = self.env["hr.attendance"]
                att_ids = Attendance.sudo().search(
                    [("id", "in", dictIds["in_altered_ids"])],
                )
                for att in att_ids:
                    if att.check_in < lv.date_to and att.check_out > lv.date_to:
                        att.check_in = lv.date_to + timedelta(seconds=1)
                    elif att.check_in < lv.date_to and att.check_out <= lv.date_to:
                        _unlink_ids |= att
                    if _unlink_ids:
                        _unlink_ids.unlink()
            if len(dictIds["out_altered_ids"]) > 0:
                _unlink_ids = self.env["hr.attendance"]
                att_ids = Attendance.sudo().search(
                    [("id", "in", dictIds["out_altered_ids"])],
                )
                for att in att_ids:
                    if att.check_out > lv.date_from and att.check_in < lv.date_from:
                        att.check_out = lv.date_from - timedelta(seconds=1)
                    elif att.check_out <= lv.date_from and att.check_in < lv.date_from:
                        _unlink_ids |= att
                    if _unlink_ids:
                        _unlink_ids.unlink()

        return res

    def adjust_schedule_by_leave(self):
        """Returns a dictionary of hr.attendance records:
        {
            'removed_ids': []       # record ids related to removed shifts
            'in_altered_ids': []    # record ids who's check-in was altered
            'out_altered_ids': []   # record ids who's check-out was altered
        }
        """

        res = {
            "removed_ids": [],
            "in_altered_ids": [],
            "out_altered_ids": [],
        }
        unlink_ids = self.env["resource.schedule.shift"]
        Shift = self.env["resource.schedule.shift"]
        for leave in self:

            shifts = Shift.search(
                [
                    ("employee_id", "=", leave.employee_id.id),
                    ("datetime_start", "<=", leave.date_to),
                    ("datetime_end", ">=", leave.date_from),
                ],
                order="datetime_start",
            )
            for shift in shifts:

                # Remove shifts completely covered by leave
                if (
                    leave.date_from <= shift.datetime_start
                    and leave.date_to >= shift.datetime_end
                ):
                    if shift not in unlink_ids:
                        unlink_ids |= shift

                # Partial day on first day of leave
                elif (
                    leave.date_from > shift.datetime_start
                    and leave.date_from <= shift.datetime_end
                ):
                    dtLv = leave.date_from
                    if (
                        leave.date_from == shift.datetime_end
                        and shift not in unlink_ids
                    ):
                        unlink_ids |= shift
                    else:
                        shift.sudo().datetime_end = dtLv + timedelta(seconds=-1)
                        res["out_altered_ids"] += shift.sudo().hr_attendance_ids.ids

                # Partial day on last day of leave
                elif (
                    leave.date_to < shift.datetime_end
                    and leave.date_to >= shift.datetime_start
                ):
                    dtLv = leave.date_to
                    if leave.date_to != shift.datetime_start:
                        shift.sudo().datetime_start = dtLv + timedelta(seconds=+1)
                        res["in_altered_ids"] += shift.sudo().hr_attendance_ids.ids

        att_ids = []
        for shift in unlink_ids:
            att_ids += shift.sudo().hr_attendance_ids.ids
        res["removed_ids"] = att_ids
        unlink_ids.sudo().unlink()
        return res
