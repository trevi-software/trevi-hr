from odoo.exceptions import AccessError
from odoo.tests.common import Form, SavepointCase


class TestHrJobWizard(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestHrJobWizard, cls).setUpClass()
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
                "groups_id": [(4, cls.group_hr_user.id)],
            }
        )
        cls.hr_officer = cls.User.create(
            {
                "name": "Hr Officer",
                "login": "hrofficer",
                "groups_id": [(4, cls.group_hr_manager.id)],
            }
        )

    def create_job_position(self):

        return self.Job.create(
            [
                {
                    "name": "#Sales Associate",
                    "no_of_recruitment": 4,
                    "no_of_hired_employee": 2,
                    "state": "recruit",
                },
                {
                    "name": "#Store Manager",
                    "no_of_recruitment": 2,
                    "no_of_hired_employee": 1,
                    "state": "recruit",
                },
                {
                    "name": "#Product Manager",
                    "no_of_recruitment": 2,
                    "no_of_hired_employee": 0,
                    "state": "recruit",
                },
            ]
        )

    def test_only_manager_can_change_recruitment_state(self):
        jobs = self.create_job_position()

        with self.assertRaises(AccessError):
            with Form(
                self.Wizard.with_user(self.hr_user).with_context(
                    {"active_ids": jobs.ids}
                )
            ) as wizard1:
                for job in wizard1.job_ids:
                    self.assertIn(job, jobs)

        with Form(
            self.Wizard.with_user(self.hr_officer).with_context(
                {"active_ids": jobs.ids}
            )
        ) as wizard2:
            for job in wizard2.job_ids:
                self.assertIn(job, jobs)

    def test_can_change_multiple_job_position_state(self):

        jobs = self.create_job_position()
        for job in jobs:
            self.assertEqual(job.state, "recruit")

        ManWiz = (
            self.Wizard.with_user(self.hr_officer)
            .with_context({"active_ids": jobs.ids})
            .create({})
        )
        for job in ManWiz.job_ids:
            self.assertIn(job, jobs)

        with Form(ManWiz) as wizard:
            wizard.do_open = True

        ManWiz.change_state()

        for job in jobs:
            self.assertEqual(job.state, "open")
            self.assertIn(job, ManWiz.job_ids)
