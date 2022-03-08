# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import fields, models


class HrHolidays(models.Model):

    _inherit = "hr.holidays"

    def holidays_validate(self):

        res = super(HrHolidays, self).holidays_validate()

        att_ids = []
        Attendance = self.env["hr.attendance"]
        for lv in self:
            if lv.type == "remove" and lv.holiday_type == "employee":
                att_ids = Attendance.search(
                    [
                        ("employee_id", "=", lv.employee_id.id),
                        ("check_in", "<=", lv.date_do),
                        ("check_out", ">=", lv.date_from),
                    ],
                    order="name",
                )

            # Adjust schedule around the leave
            self.adjust_schedule_by_leave()

            if len(att_ids) > 0:

                # Remove attendance records. Make sure to save the day so we can
                # re-create the leaves afterward.
                att_days = []
                for att in att_ids:
                    if att.day not in att_days:
                        att_days.append(att.day)
                att_ids.unlink()

                # Re-create attendance around leave
                Schedule = self.env["hr.schedule"]
                for day_str in att_days:
                    Schedule.create_attendance_from_schedule(lv.employee_id.id, day_str)
        return res

    def adjust_schedule_by_leave(self):

        unlink_ids = []
        ScheduleDetail = self.env["hr.schedule.detail"]
        for leave in self:
            if leave.type != "remove":
                continue

            det_ids = ScheduleDetail.search(
                [
                    ("schedule_id.employee_id", "=", leave.employee_id.id),
                    ("date_start", "<=", leave.date_to),
                    ("date_end", ">=", leave.date_from),
                ],
                order="date_start",
            )
            for detail in det_ids:

                # Remove schedule details completely covered by leave
                if (
                    leave.date_from <= detail.date_start
                    and leave.date_to >= detail.date_end
                ):
                    if detail.id not in unlink_ids:
                        unlink_ids.append(detail.id)

                # Partial day on first day of leave
                elif (
                    leave.date_from > detail.date_start
                    and leave.date_from <= detail.date_end
                ):
                    dtLv = fields.Datetime.from_string(leave.date_from)
                    if (
                        leave.date_from == detail.date_end
                        and detail.id not in unlink_ids
                    ):
                        unlink_ids.append(detail.id)
                    else:
                        dtSchedEnd = dtLv + timedelta(seconds=-1)
                        detail.date_end = fields.Datetime.to_string(dtSchedEnd)

                # Partial day on last day of leave
                elif (
                    leave.date_to < detail.date_end
                    and leave.date_to >= detail.date_start
                ):
                    dtLv = fields.Datetime.from_string(leave.date_to)
                    if leave.date_to != detail.date_start:
                        dtStart = dtLv + timedelta(seconds=+1)
                        detail.date_start = fields.Datetime.to_string(dtStart)

        ScheduleDetail.browse(unlink_ids).unlink()

        return

    def holidays_refuse(self):

        res = super(HrHolidays, self).holidays_refuse()

        Schedule = self.env["hr.schedule"]
        for leave in self:
            if leave.type != "remove":
                continue

            dLvFrom = fields.Datetime.from_string(leave.date_from)
            dLvTo = fields.Datetime.from_string(leave.date_to)
            sched_ids = Schedule.search(
                [
                    ("employee_id", "=", leave.employee_id.id),
                    ("date_start", "<=", fields.Date.to_string(dLvTo)),
                    ("date_end", ">=", fields.Date.to_string(dLvFrom)),
                ]
            )

            # Re-create affected schedules from scratch
            sched_ids.delete_details()
            sched_ids.create_details()

        return res
