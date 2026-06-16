# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import SavepointCase


class TestHrInfraction(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestHrInfraction, cls).setUpClass()

        # Models
        cls.Users = cls.env["res.users"]
        cls.Employee = cls.env["hr.employee"]
        cls.HrJob = cls.env["hr.job"]
        cls.Contract = cls.env["hr.contract"]
        cls.Department = cls.env["hr.department"]
        cls.Transfer = cls.env["hr.department.transfer"]
        cls.Infraction = cls.env["hr.infraction"]
        cls.InfractionAction = cls.env["hr.infraction.action"]
        cls.InfractionCategory = cls.env["hr.infraction.category"]
        cls.InfractionWarning = cls.env["hr.infraction.warning"]
        cls.InfActWizard = cls.env["hr.infraction.action.wizard"]
        cls.InfBatch = cls.env["hr.infraction.batch"]

        # groups and users
        cls.group_base_system = cls.env.ref("base.group_system")
        cls.group_hr_user = cls.env.ref("hr.group_hr_user")
        cls.group_hr_manager = cls.env.ref("hr.group_hr_manager")
        cls.group_hr_contract_manager = cls.env.ref(
            "hr_contract.group_hr_contract_manager"
        )
        cls.group_inf_entry = cls.env.ref("hr_infraction.group_hr_infraction_entry")
        cls.group_inf_approve = cls.env.ref("hr_infraction.group_hr_infraction_approve")
        cls.group_payroll_mgr = cls.env.ref(
            "group_payroll_manager.group_payroll_manager"
        )

        cls.user_simple = cls.Users.create(
            {
                "name": "#HR User",
                "login": "#hr_user",
                "groups_id": [(4, cls.group_hr_user.id)],
            }
        )
        cls.user_entry = cls.Users.create(
            {
                "name": "#Inf Entry",
                "login": "#tinf_entry",
                "groups_id": [(4, cls.group_inf_entry.id)],
            }
        )
        cls.user_approve = cls.Users.create(
            {
                "name": "#Inf Approve",
                "login": "#tinf_approve",
                "groups_id": [
                    (4, cls.group_base_system.id),
                    (4, cls.group_inf_approve.id),
                    (4, cls.group_payroll_mgr.id),
                    (4, cls.group_hr_contract_manager.id),
                ],
            }
        )
        cls.user_hr_manager = cls.Users.create(
            {
                "name": "#Hr Mgr",
                "login": "#hr_mgr",
                "groups_id": [
                    (4, cls.group_base_system.id),
                    (4, cls.group_inf_approve.id),
                    (4, cls.group_payroll_mgr.id),
                    (4, cls.group_hr_contract_manager.id),
                ],
            }
        )

        cls.user_simple.action_create_employee()
        cls.user_entry.action_create_employee()
        cls.user_approve.action_create_employee()
        cls.user_hr_manager.action_create_employee()

        # test records and data
        cls.employee = cls.Employee.with_user(cls.user_approve).create(
            {"name": "#John", "parent_id": cls.user_approve.employee_id.id}
        )
        cls.dept_hr = cls.Department.create({"name": "#Research & Development"})
        cls.job_senior = cls.HrJob.create(
            {"name": "Senior Researcher", "department_id": cls.dept_hr.id}
        )
        cls.job_junior = cls.HrJob.create(
            {"name": "Junior Researcher", "department_id": cls.dept_hr.id}
        )
        cls.dstart = fields.Date.today()
        cls.dend = fields.Date.today() + timedelta(days=90)

    def create_contract(
        self,
        state,
        kanban_state,
        start,
        end=None,
        trial_end=None,
        employee=None,
        user=None,
    ):
        _user = self.user_entry if not user else user
        _employee = self.employee if not employee else employee
        return (
            self.env["hr.contract"]
            .with_user(_user)
            .create(
                {
                    "name": "Contract",
                    "employee_id": _employee.id,
                    "state": state,
                    "kanban_state": kanban_state,
                    "job_id": self.job_senior.id,
                    "wage": 1,
                    "date_start": start,
                    "trial_date_end": trial_end,
                    "date_end": end,
                }
            )
        )

    def create_infraction(self, employee=None, user=None):
        _user = self.user_entry if not user else user
        _employee = self.employee if not employee else employee
        return self.Infraction.with_user(_user).create(
            {
                "name": "Infraction #1",
                "date": fields.Date.today(),
                "employee_id": _employee.id,
                "category_id": self.env.ref(
                    "hr_infraction.infraction_category_care"
                ).id,
                "state": "draft",
            }
        )

    def test_cant_remove_infraction_past_draft_state(self):
        self.create_contract(
            "draft", "normal", self.dstart, user=self.user_approve
        ).signal_confirm()
        infraction = self.create_infraction(user=self.user_entry)
        self.assertEqual(infraction.state, "draft")
        infraction.action_confirm()
        with self.assertRaises(UserError):
            infraction.unlink()

    def test_infraction_termination_action(self):
        self.create_contract(
            "draft",
            "normal",
            self.dstart,
            employee=self.user_approve.employee_id,
            user=self.user_approve,
        ).signal_confirm()
        infraction = self.create_infraction(
            self.user_approve.employee_id, user=self.user_entry
        )
        infraction.action_confirm()

        self.assertEqual(infraction.state, "confirm")
        self.assertEqual(infraction.employee_id.contract_id.state, "open")

        self.InfActWizard.with_user(self.user_approve).with_context(
            {"active_id": infraction.id}
        ).create(
            {"action_type": "dismissal", "effective_date": fields.Date.today()}
        ).create_action()

        self.assertEqual(infraction.state, "action")
        self.assertEqual(infraction.employee_id.contract_id.state, "close")

        for contract in infraction.employee_id.contract_ids:
            self.assertEqual(contract.state, "close")

    def test_infraction_transfer_action(self):
        self.create_contract(
            "draft",
            "normal",
            self.dstart,
            employee=self.user_approve.employee_id,
            user=self.user_approve,
        ).signal_confirm()
        infraction = self.create_infraction(
            self.user_approve.employee_id, user=self.user_entry
        )
        infraction.action_confirm()

        self.assertEqual(infraction.state, "confirm")
        self.assertEqual(infraction.employee_id.contract_id.state, "open")

        self.InfActWizard.with_user(self.user_approve).with_context(
            {"active_id": infraction.id}
        ).create(
            {
                "action_type": "transfer",
                "new_job_id": self.job_junior.id,
                "xfer_effective_date": (fields.Date.today() - timedelta(days=1)),
            }
        ).create_action()
        transfer = self.Transfer.search([], limit=1)
        self.assertFalse(len(transfer) == 0)
        self.assertEqual(transfer.state, "draft")

    def test_cant_remove_warnings_attached_to_confirmed_infraction(self):
        self.create_contract("draft", "normal", self.dstart, user=self.user_approve)
        infraction = self.create_infraction(user=self.user_entry)
        infraction.action_confirm()
        self.InfActWizard.with_context({"active_id": infraction.id}).create(
            {
                "action_type": "warning_verbal",
            }
        ).create_action()
        with self.assertRaises(UserError):
            inf_action = self.InfractionAction.search(
                [("infraction_id", "=", infraction.id)]
            )
            inf_waring = self.InfractionWarning.search(
                [("action_id", "=", inf_action.id)]
            )
            inf_waring.unlink()
        self.assertEqual(infraction.state, "action")

    def test_cont_remove_action_attached_to_confirmed_infraction(self):
        self.create_contract("draft", "normal", self.dstart, user=self.user_approve)
        infraction = self.create_infraction(user=self.user_entry)
        infraction.action_confirm()
        self.assertEqual(infraction.state, "confirm")
        self.InfActWizard.with_user(self.user_approve).with_context(
            {"active_id": infraction.id}
        ).create({"action_type": "warning_verbal"}).create_action()
        with self.assertRaises(UserError):
            inf_action = self.InfractionAction.search(
                [("infraction_id", "=", infraction.id)]
            )
            inf_action.unlink()
        self.assertEqual(infraction.state, "action")

    def test_only_approveal_group_member_can_take_action(self):
        self.create_contract("draft", "normal", self.dstart, user=self.user_approve)
        infraction = self.create_infraction(user=self.user_entry)
        infraction.action_confirm()
        self.assertEqual(infraction.state, "confirm")

        with self.assertRaises(AccessError):
            self.InfActWizard.with_user(self.user_simple).with_context(
                {"active_id": infraction.id}
            ).create({"action_type": "warning_verbal"}).create_action()

        with self.assertRaises(AccessError):
            self.InfActWizard.with_user(self.user_entry).with_context(
                {"active_id": infraction.id}
            ).create({"action_type": "warning_verbal"}).create_action()

        self.InfActWizard.with_user(self.user_approve).with_context(
            {"active_id": infraction.id}
        ).create({"action_type": "warning_verbal"}).create_action()

        self.assertEqual(infraction.state, "action")

    def test_infraction_action_for_own_rule(self):
        self.create_contract(
            "draft",
            "normal",
            self.dstart,
            employee=self.user_approve.employee_id,
            user=self.user_approve,
        )
        infraction = self.create_infraction(
            employee=self.user_approve.employee_id, user=self.user_entry
        )
        infraction.action_confirm()
        self.assertEqual(infraction.state, "confirm")

        # non-subordinate action attempt
        with self.assertRaises(AccessError):
            self.InfActWizard.with_user(self.user_hr_manager).with_context(
                {"active_id": infraction.id}
            ).create({"action_type": "warning_verbal"}).create_action()

        self.InfActWizard.with_user(self.user_approve).with_context(
            {"active_id": infraction.id}
        ).create({"action_type": "warning_verbal"}).create_action()

        self.assertEqual(infraction.state, "action")

    def test_infraction_action_for_subordinates_rule(self):
        self.create_contract("draft", "normal", self.dstart, user=self.user_approve)
        infraction = self.create_infraction(user=self.user_entry)
        infraction.action_confirm()
        self.assertEqual(infraction.state, "confirm")

        # non-subordinate action attempt
        with self.assertRaises(AccessError):
            self.InfActWizard.with_user(self.user_hr_manager).with_context(
                {"active_id": infraction.id}
            ).create({"action_type": "warning_verbal"}).create_action()

        self.InfActWizard.with_user(self.user_approve).with_context(
            {"active_id": infraction.id}
        ).create({"action_type": "warning_verbal"}).create_action()

        self.assertEqual(infraction.state, "action")
