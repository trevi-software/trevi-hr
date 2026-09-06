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
        # In 18.0, write access on hr.job belongs to hr_recruitment groups
        cls.group_recruitment_manager = cls.env.ref(
            "hr_recruitment.group_hr_recruitment_manager"
        )

        # -- Users
        cls.hr_user = cls.User.create(
            {
                "name": "Hr User",
                "login": "hruser",
                "groups_id": [(4, cls.group_hr_user.id)],
            }
        )
        cls.hr_officer = cls.User.create(
            {
                "name": "Hr Officer",
                "login": "hrofficer",
                "groups_id": [
                    (4, cls.group_hr_manager.id),
                    (4, cls.group_recruitment_manager.id),
                ],
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
