# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime, timedelta

from odoo.tests import common


class TestHrAttendance(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.HrAttendance = cls.env["hr.attendance"]
        cls.HrEmployee = cls.env["hr.employee"]

        cls.employee = cls.HrEmployee.create({"name": "John"})
        cls.eeSally = cls.HrEmployee.create({"name": "Sally"})

    def test_auto_punchout(self):

        self.env["ir.config_parameter"].set_param(
            "resource_schedule.max_shift_length", 15
        )
        today = date.today()
        att = self.HrAttendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime.combine(
                    today, datetime.strptime("05:00", "%H:%M").time()
                ),
            }
        )

        now = datetime.combine(today, datetime.strptime("19:59", "%H:%M").time())
        res = self.HrAttendance._auto_punchout(now)

        self.assertEqual(res, self.HrAttendance, "The returned attendace is empty")
        self.assertFalse(
            att.check_out,
            "The attendance hasn't been punched out because it's not yet max shift length",
        )

        self.env["ir.config_parameter"].set_param(
            "resource_schedule.max_shift_length", 0
        )
        now = datetime.combine(today, datetime.strptime("23:00", "%H:%M").time())
        res = self.HrAttendance._auto_punchout(now)
        self.assertFalse(
            att.check_out,
            "The attendance hasn't been punched out because max shift length hasn't been set",
        )

        att2 = self.HrAttendance.create(
            {
                "employee_id": self.eeSally.id,
                "check_in": datetime.combine(
                    today, datetime.strptime("03:00", "%H:%M").time()
                ),
            }
        )

        self.env["ir.config_parameter"].set_param(
            "resource_schedule.max_shift_length", 15
        )
        now = datetime.combine(today, datetime.strptime("23:00", "%H:%M").time())
        res = self.HrAttendance._auto_punchout(now)
        self.assertEqual(
            res, att + att2, "The returned attendace item is the one I created"
        )
        self.assertEqual(
            res[0].check_out,
            datetime.combine(today, datetime.strptime("20:00", "%H:%M").time()),
            "The attendance record has been clocked out after 15 hours",
        )
        self.assertEqual(
            att2.check_out,
            datetime.combine(today, datetime.strptime("18:00", "%H:%M").time()),
            "Sally's attendance has been clocked out 15 hours after *its* start",
        )

    def test_auto_punchout2(self):

        check_in = datetime.now() - timedelta(hours=14)
        att = self.HrAttendance.create(
            {"employee_id": self.employee.id, "check_in": check_in}
        )

        self.HrAttendance.auto_punchout()
        self.assertFalse(
            att.check_out,
            "The attendance hasn't been punched out because it's not yet max shift length",
        )

        check_in = datetime.now() - timedelta(hours=16)
        att.check_in = check_in
        self.HrAttendance.auto_punchout()
        self.assertEqual(
            att.check_out,
            check_in + timedelta(hours=15),
            "The attendance record has been clocked out after 15 hours",
        )
