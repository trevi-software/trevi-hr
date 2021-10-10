# Copyright (C) 2021 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user


class TestPolicyAccess(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPolicyAccess, cls).setUpClass()

        cls.OtPolicy = cls.env["hr.policy.ot"]
        cls.OtPolicyLine = cls.env["hr.policy.line.ot"]
        cls.ot_policy = cls.OtPolicy.create({"name": "OT1", "date": date.today()})
        cls.ot_line = cls.OtPolicyLine.create(
            {
                "name": "Line1",
                "code": "L1",
                "type": "daily",
                "policy_id": cls.ot_policy.id,
            }
        )
        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="pm",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
            email="ric@example.com",
        )
        # Payroll user
        cls.userPU = new_test_user(
            cls.env,
            login="pu",
            groups="base.group_user,payroll.group_payroll_user",
            name="Payroll manager",
            email="ric@example.com",
        )
        # HR Manager
        cls.userHRM = new_test_user(
            cls.env,
            login="hrm",
            groups="base.group_user,hr.group_hr_manager",
            name="Payroll manager",
            email="ric@example.com",
        )

    def test_hrm_access(self):
        """HRM only has read access"""

        # Create fails
        with self.assertRaises(AccessError):
            self.OtPolicy.with_user(self.userHRM).create(
                {"name": "OT2", "date": date.today()}
            )
            self.OtPolicyLine.with_user(self.userHRM).create(
                {"name": "line2", "type": "daily"}
            )
        # Unlink fails
        with self.assertRaises(AccessError):
            self.ot_policy.with_user(self.userHRM).unlink()
            self.ot_line.with_user(self.userHRM).unlink()
        # Read succeeds
        try:
            self.OtPolicy.with_user(self.userHRM).browse(self.ot_policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.ot")
        try:
            self.OtPolicyLine.with_user(self.userHRM).browse(self.ot_policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.line.ot")
        # Write fails
        with self.assertRaises(AccessError):
            self.OtPolicy.with_user(self.userHRM).browse(self.ot_policy.id).write(
                {"name": "OT3"}
            )
            self.OtPolicyLine.with_user(self.userHRM).browse(self.ot_line.id).write(
                {"name": "line3"}
            )

    def test_payroll_user_access(self):
        """Payroll User only has read access"""

        # Create fails
        with self.assertRaises(AccessError):
            self.OtPolicy.with_user(self.userPU).create(
                {"name": "OT2", "date": date.today()}
            )
            self.OtPolicyLine.with_user(self.userPU).create(
                {"name": "line2", "type": "daily"}
            )
        # Unlink fails
        with self.assertRaises(AccessError):
            self.ot_policy.with_user(self.userPU).unlink()
            self.ot_line.with_user(self.userPU).unlink()
        # Read succeeds
        try:
            self.OtPolicy.with_user(self.userPU).browse(self.ot_policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.ot")
        try:
            self.OtPolicyLine.with_user(self.userPU).browse(self.ot_policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.line.ot")
        # Write fails
        with self.assertRaises(AccessError):
            self.OtPolicy.with_user(self.userPU).browse(self.ot_policy.id).write(
                {"name": "OT3"}
            )
            self.OtPolicyLine.with_user(self.userPU).browse(self.ot_line.id).write(
                {"name": "line3"}
            )

    def test_payroll_manager_access(self):
        """Payroll Manager has complete access"""

        # Read succeeds
        try:
            self.OtPolicy.with_user(self.userPM).browse(self.ot_policy.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.ot")
        try:
            self.OtPolicyLine.with_user(self.userPM).browse(self.ot_line.id)
        except AccessError:
            self.fail("Caught an unexpected exception reading hr.policy.line.ot")
        # Write succeeds
        try:
            self.OtPolicy.with_user(self.userPM).browse(self.ot_policy.id).write(
                {"name": "XX"}
            )
        except AccessError:
            self.fail("Caught an unexpected exception writing hr.policy.ot")
        try:
            self.OtPolicyLine.with_user(self.userPM).browse(self.ot_line.id).write(
                {"name": "XX"}
            )
        except AccessError:
            self.fail("Caught an unexpected exception writing hr.policy.line.ot")
        # Create/Unlink succeeds
        try:
            ot = self.OtPolicy.with_user(self.userPM).create(
                {"name": "OT test pm", "date": date.today()}
            )
            ot.unlink()
        except AccessError:
            self.fail("Caught unexpected exception creating/unlinking hr.policy.ot")
        try:
            line = self.OtPolicyLine.with_user(self.userPM).create(
                {"name": "line test pm", "type": "daily", "code": "A"}
            )
            line.unlink()
        except AccessError:
            self.fail(
                "Caught unexpected exception creating/unlinking hr.policy.line.ot"
            )
