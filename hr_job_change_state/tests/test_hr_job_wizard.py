from odoo.exceptions import AccessError
from odoo.tests import Form, TransactionCase


class TestHrJobWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Job = cls.env["hr.job"]
        cls.Wizard = cls.env["hr.job.wizard.state.change"]
        cls.User = cls.env["res.users"]

        cls.group_hr_manager = cls.env.ref("hr.group_hr_manager")
        cls.group_hr_user = cls.env.ref("hr.group_hr_user")

        # -- Users
        cls.hr_user = cls.User.create(
            {
                "name": "Hr User",
                "login": "hruser",
                "group_ids": [(4, cls.group_hr_user.id)],
            }
        )
        cls.hr_officer = cls.User.create(
            {
                "name": "Hr Officer",
                "login": "hrofficer",
                "group_ids": [(4, cls.group_hr_manager.id)],
            }
        )

    def create_job_position(self):
        # hr_contract_status makes hr.job.department_id required
        department = self.env["hr.department"].create({"name": "#Test Dept"})
        return self.Job.create(
            [
                {
                    "name": "#Sales Associate",
                    "no_of_recruitment": 4,
                    "state": "recruit",
                    "department_id": department.id,
                },
                {
                    "name": "#Store Manager",
                    "no_of_recruitment": 2,
                    "state": "recruit",
                    "department_id": department.id,
                },
                {
                    "name": "#Product Manager",
                    "no_of_recruitment": 2,
                    "state": "recruit",
                    "department_id": department.id,
                },
            ]
        )

    def test_only_manager_can_change_recruitment_state(self):
        jobs = self.create_job_position()

        with (
            self.assertRaises(AccessError),
            Form(
                self.Wizard.with_user(self.hr_user).with_context(active_ids=jobs.ids)
            ) as wizard1,
        ):
            for job in wizard1.job_ids:
                self.assertIn(job, jobs)

        with self.assertRaises(AccessError):
            jobs.with_user(self.hr_user).set_open()

        with Form(
            self.Wizard.with_user(self.hr_officer).with_context(active_ids=jobs.ids)
        ) as wizard2:
            for job in wizard2.job_ids:
                self.assertIn(job, jobs)

    def test_can_change_multiple_job_position_state(self):
        jobs = self.create_job_position()
        for job in jobs:
            self.assertEqual(job.state, "recruit")

        wizard = (
            self.Wizard.with_user(self.hr_officer)
            .with_context(active_ids=jobs.ids)
            .create({})
        )
        for job in wizard.job_ids:
            self.assertIn(job, jobs)

        with Form(wizard) as wizard_form:
            wizard_form.do_open = True

        wizard.change_state()

        for job in jobs:
            self.assertEqual(job.state, "open")
            self.assertIn(job, wizard.job_ids)

    def test_change_state_button_only_for_managers(self):
        """The wizard button must not be offered to users who cannot use it.

        The wizard's only ACL entry grants hr.group_hr_manager, so showing the
        button to other HR users sends them straight into an AccessError.
        """

        button = "Change Recruitment State"

        arch_manager = self.Job.with_user(self.hr_officer).get_view(view_type="list")[
            "arch"
        ]
        self.assertIn(button, arch_manager, "An HR manager is offered the button")

        arch_user = self.Job.with_user(self.hr_user).get_view(view_type="list")["arch"]
        self.assertNotIn(
            button,
            arch_user,
            "A user who cannot use the wizard is not offered the button",
        )
