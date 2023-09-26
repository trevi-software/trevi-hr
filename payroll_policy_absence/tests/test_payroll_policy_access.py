# Copyright (C) 2021 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestPolicyAccess(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPolicyAccess, cls).setUpClass()

        cls.Policy = cls.env["hr.policy.absence"]
        cls.PolicyLine = cls.env["hr.policy.line.absence"]
        cls.leave_type = cls.env.ref("hr_holidays.holiday_status_cl")
        cls.policy = cls.Policy.create({"name": "POLICY1", "date": date.today()})
        cls.line = cls.PolicyLine.create(
            {
                "name": "Line1",
                "code": "L1",
                "type": "paid",
                "holiday_status_id": cls.leave_type.id,
                "policy_id": cls.policy.id,
            }
        )
        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="pm",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
            email="pm@example.com",
        )
        # Payroll user
        cls.userPU = new_test_user(
            cls.env,
            login="pu",
            groups="base.group_user,payroll.group_payroll_user",
            name="Payroll manager",
            email="pu@example.com",
        )
        # HR Manager
        cls.userHRM = new_test_user(
            cls.env,
            login="hrm",
            groups="base.group_user,hr.group_hr_manager",
            name="Payroll manager",
            email="hrm@example.com",
        )

    def test_hrm_access(self):
        """HRM only has read access"""

        # Create fails
        with self.assertRaises(AccessError):
            self.Policy.with_user(self.userHRM).create(
                {"name": "POLICY2", "date": date.today()}
            )
            self.OtPolicyLine.with_user(self.userHRM).create(
                {"name": "line2", "type": "daily"}
            )
        # Unlink fails
        with self.assertRaises(AccessError):
            self.policy.with_user(self.userHRM).unlink()
            self.line.with_user(self.userHRM).unlink()
        # Read succeeds
        try:
            self.Policy.with_user(self.userHRM).browse(self.policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.presence")
        try:
            self.PolicyLine.with_user(self.userHRM).browse(self.policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.line.presence")
        # Write fails
        with self.assertRaises(AccessError):
            self.Policy.with_user(self.userHRM).browse(self.policy.id).write(
                {"name": "POLICY3"}
            )
            self.PolicyLine.with_user(self.userHRM).browse(self.line.id).write(
                {"name": "line3"}
            )

    def test_payroll_user_access(self):
        """Payroll User only has read access"""

        # Create fails
        with self.assertRaises(AccessError):
            self.Policy.with_user(self.userPU).create(
                {"name": "POL2", "date": date.today()}
            )
            self.PolicyLine.with_user(self.userPU).create(
                {"name": "line2", "type": "daily"}
            )
        # Unlink fails
        with self.assertRaises(AccessError):
            self.policy.with_user(self.userPU).unlink()
            self.line.with_user(self.userPU).unlink()
        # Read succeeds
        try:
            self.Policy.with_user(self.userPU).browse(self.policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.presence")
        try:
            self.PolicyLine.with_user(self.userPU).browse(self.policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.line.presence")
        # Write fails
        with self.assertRaises(AccessError):
            self.Policy.with_user(self.userPU).browse(self.policy.id).write(
                {"name": "POL3"}
            )
            self.PolicyLine.with_user(self.userPU).browse(self.line.id).write(
                {"name": "line3"}
            )

    def test_payroll_manager_access(self):
        """Payroll Manager has complete access"""

        # Read succeeds
        try:
            self.Policy.with_user(self.userPM).browse(self.policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.presence")
        try:
            self.PolicyLine.with_user(self.userPM).browse(self.line.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.line.presence")
        # Write succeeds
        try:
            self.Policy.with_user(self.userPM).browse(self.policy.id).write(
                {"name": "XX"}
            )
        except AccessError:
            self.fail("Caught an unexpected exception writing hr.policy.presence")
        try:
            self.PolicyLine.with_user(self.userPM).browse(self.line.id).write(
                {"name": "XX"}
            )
        except AccessError:
            self.fail("Caught an unexpected exception writing hr.policy.line.presence")
        # Create/Unlink succeeds
        try:
            pol = self.Policy.with_user(self.userPM).create(
                {"name": "Policy test pm", "date": date.today()}
            )
            pol.unlink()
        except AccessError:
            self.fail(
                "Caught unexpected exception creating/unlinking hr.policy.presence"
            )
        try:
            line = self.PolicyLine.with_user(self.userPM).create(
                {
                    "name": "line test pm",
                    "code": "A",
                    "type": "paid",
                    "holiday_status_id": self.leave_type.id,
                }
            )
            line.unlink()
        except AccessError:
            self.fail(
                "Caught unexpected exception creating/unlinking hr.policy.line.presence"
            )
