# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, exceptions, fields, models


class HrAttendance(models.Model):

    _inherit = "hr.employee"

    # Completely over-ride base module method to implement rounding.
    # Base module: hr_attendance/models/hr_employee.py
    #
    def _attendance_action_change(self):
        """Check In/Check Out action
        Check In: create a new attendance record
        Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = fields.Datetime.now()

        if self.attendance_state != "checked_in":
            vals = {
                "employee_id": self.id,
                "clock_in": action_date,
            }
            return self.env["hr.attendance"].create(vals)
        attendance = self.env["hr.attendance"].search(
            [("employee_id", "=", self.id), ("check_out", "=", False)], limit=1
        )
        if attendance:
            attendance.clock_out = action_date
        else:
            raise exceptions.UserError(
                _(
                    "Cannot perform check out on %(empl_name)s, "
                    "could not find corresponding check in. "
                    "Your attendances have probably been modified "
                    "manually by human resources."
                )
                % {
                    "empl_name": self.sudo().name,
                }
            )
        return attendance
