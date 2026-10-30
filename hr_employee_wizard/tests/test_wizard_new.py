# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase


class RecruitmentTestCase(TransactionCase):
    def setUp(self):
        super().setUp()

        self.Version = self.env["hr.version"]
        self.Partner = self.env["res.partner"]
        self.Period = self.env["hr.payroll.period"]
        self.PPSchedule = self.env["hr.payroll.period.schedule"]
        self.PolicyGroup = self.env["hr.policy.group"]
        self.labour_model = self.env["hr.employee.wizard.new"]
        benefits_model = self.env["hr.employee.wizard.benefit"]
        self.company = self.env.user.company_id
        self.state = self.env["res.country.state"].search([], limit=1)
        self.country = self.env["res.country"].search([], limit=1)
        # Odoo 19 does not install demo data: create the records the wizard needs.
        self.department = self.env["hr.department"].create(
            {"name": "Bridge", "company_id": self.company.id}
        )
        self.job = self.env["hr.job"].create(
            {
                "name": "Captain",
                "company_id": self.company.id,
                "department_id": self.department.id,
            }
        )
        self.structure = self.env["hr.payroll.structure"].create({"name": "Base"})
        self.pps = self.create_payroll_schedule("monthly", date.today())  # noqa: DTZ011
        self.pgroup = self.PolicyGroup.create({"name": "PGroup"})
        # The 44h/week working schedule only exists in resource_schedule's demo
        # data, which is not installed in CI. Build an equivalent one from the
        # module's regular attendance templates instead of a demo xmlid.
        morning = self.env.ref("resource_schedule.attendance_template_0")
        afternoon = self.env.ref("resource_schedule.attendance_template_1")
        self.calendar_id = self.env["resource.calendar"].create(
            {
                "name": "44 Hour/Week",
                "attendance_ids": [
                    (0, 0, {"dayofweek": str(day), "template_id": template.id})
                    for day in range(5)
                    for template in (morning, afternoon)
                ]
                + [(0, 0, {"dayofweek": "5", "template_id": morning.id})],
            }
        )
        self.benefits = self.env["hr.benefit"].create({"name": "A", "code": "A"})

        benefits_data = {
            "benefit_id": self.benefits.id,
            "effective_date": "2017-01-01",
            "end_date": "2017-12-30",
            "adv_override": True,
            "prm_override": True,
            "adv_amount": 50.0,
            "prm_amount": 100.0,
            "prm_total": 2000.0,
        }
        self.benefits_data = benefits_data
        self.benefit = benefits_model.create(benefits_data)

        self.labour_data = {
            "name": "Jean-Luc Picard",
            "new_benefit_ids": [(6, 0, [self.benefit.id])],
            "state": "personal",
            "company_id": self.company.id,
            "birth_date": "1990-01-01",
            "gender": "m",
            "id_no": "123",
            "city": "test_city",
            "state_id": self.state.id,
            "country_id": self.country.id,
            "telephone": "123456789",
            "mobile": "09124578",
            "education": "graduate",
            "job_id": self.job.id,
            "department_id": self.department.id,
            "struct_id": self.structure.id,
            "pps_id": self.pps.id,
            "policy_group_id": self.pgroup.id,
            "wage": 2000,
            "calendar_id": self.calendar_id.id,
            "date_start": "2017-01-01",
            "date_end": "2017-12-30",
            "trial_date_end": "2017-03-30",
        }

    def create_wizard(self):
        ctx = self.env.context.copy()
        ctx["csdate"] = self.labour_data["date_start"]
        return self.labour_model.with_context(**ctx).create(self.labour_data)

    def create_payroll_schedule(self, stype=False, initial_date=False):
        return self.PPSchedule.create(
            {
                "name": "PPS",
                "tz": "Africa/Addis_Ababa",
                "type": stype,
                "initial_period_date": initial_date,
            }
        )

    def create_payroll_period(self, sched_id, start, end):
        return self.Period.create(
            {
                "name": "Period 1",
                "schedule_id": sched_id,
                "date_start": start,
                "date_end": end,
            }
        )

    def test_create_partner(self):
        wizard = self.create_wizard()
        wizard.create_partner()

        self.assertEqual(
            self.Partner.search_count([("name", "=", "Jean-Luc Picard")]),
            1,
            "A partner record is created for the employee",
        )

    def test_create_employee(self):
        wizard = self.create_wizard()
        wizard.hire_applicant()

        self.assertEqual(
            self.env["hr.employee"].search_count([("name", "=", "Jean-Luc Picard")]),
            1,
            "One new employee was created",
        )

        ee = self.env["hr.employee"].search([("name", "=", "Jean-Luc Picard")])
        contracts = ee.version_ids.filtered("contract_date_start")
        self.assertEqual(len(contracts), 1, "The newly created employee has a contract")
        self.assertTrue(
            ee.applicant_ids, "A candidate record is attached to the employee"
        )
        self.assertEqual(
            ee.applicant_ids.partner_id.address_get(["contact"])["contact"],
            ee.work_contact_id.id,
            "The employee home address is correct",
        )
        self.assertEqual(ee.sex, "male", "Gender field set according to wizard")
        self.assertEqual(
            ee.birthday, date(1990, 1, 1), "Birth date set according to wizard"
        )
        self.assertEqual(
            ee.identification_id, "123", "Official ID set according to wizard"
        )
        self.assertEqual(ee.job_title, wizard.job_id.name, "The job title is correct")

        c = contracts
        self.assertEqual(c.job_id, wizard.job_id, "The job position is correct")
        self.assertEqual(
            c.contract_date_start,
            date(2017, 1, 1),
            "The contract start date is set according to the wizard",
        )
        self.assertEqual(
            ee.department_id, wizard.department_id, "The department is correct"
        )

    def test_required_fields(self):
        f = Form(self.env["hr.employee.wizard.new"])
        wiz = f.save()

        # name, birth date, gender are required
        with self.assertRaises(ValidationError):
            wiz.create_applicant()

        f.name = "Zaphod Beeblebrox"
        f.gender = "m"
        f.save()

        with self.assertRaises(ValidationError):
            wiz.hire_applicant()

    def test_create_applicant_returns_applicant(self):
        """Starting recruitment must open the applicant that was just created."""
        wizard = self.create_wizard()
        res = wizard.create_applicant()
        applicant = self.env["hr.applicant"].search(
            [("partner_name", "=", "Jean-Luc Picard")]
        )

        self.assertEqual(len(applicant), 1, "An applicant record was created")
        self.assertEqual(
            res["res_model"], "hr.applicant", "The action opens an applicant"
        )
        self.assertEqual(
            res["res_id"], applicant.id, "The action opens the created applicant"
        )

    def test_diploma_education(self):
        """A diploma must be accepted by the applicant and the employee."""
        applicant = self.env["hr.applicant"].create(
            {
                "partner_name": "Diploma Holder",
                "job_id": self.job.id,
                "education": "diploma",
            }
        )
        self.assertEqual(applicant.education, "diploma")

        wizard = self.create_wizard()
        wizard.education = "diploma"
        wizard.hire_applicant()

        ee = self.env["hr.employee"].search([("name", "=", "Jean-Luc Picard")])
        self.assertEqual(
            ee.certificate, "diploma", "The diploma is kept on the employee"
        )

    def test_applicant_without_gender(self):
        """An applicant without a gender must not become a male employee."""
        partner = self.Partner.create({"name": "No Gender"})
        applicant = self.env["hr.applicant"].create(
            {
                "partner_name": "No Gender",
                "partner_id": partner.id,
                "job_id": self.job.id,
            }
        )
        self.assertFalse(applicant.gender)

        res = applicant.create_employee_from_applicant()
        ee = self.env["hr.employee"].browse(res["res_id"])
        self.assertFalse(ee.sex, "No gender was recorded on the applicant")

    def test_id_no_kept_on_applicant(self):
        """The Official ID must survive on an applicant that is not hired."""
        wizard = self.create_wizard()
        wizard.create_applicant()

        applicant = self.env["hr.applicant"].search(
            [("partner_name", "=", "Jean-Luc Picard")]
        )
        self.assertEqual(
            applicant.id_no, "123", "The Official ID is kept on the applicant"
        )

    def test_past_hire_keeps_contract_details_current(self):
        """A backdated hire must not be shadowed by the initial empty version."""
        wizard = self.create_wizard()
        wizard.hire_applicant()

        ee = self.env["hr.employee"].search([("name", "=", "Jean-Luc Picard")])
        self.assertEqual(
            len(ee.version_ids),
            1,
            "The initial version is reused, not left next to a populated one",
        )
        current = ee.current_version_id
        self.assertEqual(
            current.date_version,
            date(2017, 1, 1),
            "The employee's only version is dated on the contract start date",
        )
        self.assertEqual(
            current.wage, 2000, "The current version carries the wizard's wage"
        )
        self.assertEqual(
            current.job_id, wizard.job_id, "The current version has the right job"
        )
        self.assertTrue(
            current.contract_date_start,
            "The current version is the contract the wizard created",
        )

    def test_current_hire_creates_first_shifts(self):
        """A hire in the current week must still schedule the first shifts.

        The schedule is built from the Monday of the hire's week, and the
        calendar used here has no Sunday attendance, so hire on a Monday:
        the target day is then always a working day, whatever weekday the
        suite runs on.
        """
        hire_date = date.today() + timedelta(  # noqa: DTZ011
            days=(7 - date.today().weekday()) % 7  # noqa: DTZ011
        )
        data = dict(self.labour_data)
        data.update({"date_start": hire_date, "date_end": False})
        wizard = self.labour_model.create(data)
        wizard.hire_applicant()

        ee = self.env["hr.employee"].search([("name", "=", "Jean-Luc Picard")])
        self.assertEqual(
            ee.version_ids.filtered("contract_date_start").wage,
            2000,
            "The contract details were written on the employee's version",
        )
        shifts = ee.scheduled_shift_ids
        self.assertTrue(shifts, "The first hire gets an initial shift schedule")
        self.assertEqual(
            shifts.mapped("resource_id"), ee.resource_id, "Shifts are the employee's"
        )
        self.assertIn(
            hire_date,
            shifts.mapped("day"),
            "The employee is scheduled from the day the contract starts",
        )

    def test_hire_without_scheduling_rights(self):
        """An HR officer without scheduling rights must still be able to hire.

        Hiring creates the employee's first shifts, but that is a side effect
        of the hire: the officer must not need
        ``resource_schedule.group_scheduling_user`` for it.
        """
        groups = (
            self.env.ref("base.group_user")
            | self.env.ref("hr_recruitment.group_hr_recruitment_user")
            | self.env.ref("hr.group_hr_manager")
        )
        officer = self.env["res.users"].create(
            {
                "name": "HR Officer",
                "login": "hr_officer_no_scheduling",
                "email": "officer_no_scheduling@example.com",
                "group_ids": [(6, 0, groups.ids)],
            }
        )
        self.assertFalse(
            officer.has_group("resource_schedule.group_scheduling_user"),
            "The officer must not carry the scheduling group",
        )
        hire_date = date.today() + timedelta(  # noqa: DTZ011
            days=(7 - date.today().weekday()) % 7  # noqa: DTZ011
        )
        data = dict(self.labour_data)
        data.update(
            {
                "date_start": hire_date,
                "date_end": False,
                # ``hr.employee.wizard.benefit`` is a TransientModel: linking the
                # line setUp created would ask the officer to modify another
                # user's record before the hire is even attempted. Build the line
                # with this wizard instead, as the officer's own form does.
                "new_benefit_ids": [(0, 0, dict(self.benefits_data))],
            }
        )
        wizard = self.labour_model.with_user(officer).create(data)
        wizard.hire_applicant()

        ee = self.env["hr.employee"].search([("name", "=", "Jean-Luc Picard")])
        self.assertTrue(ee, "The hire went through without scheduling rights")
        self.assertTrue(ee.scheduled_shift_ids, "The hire scheduled the first shifts")

    def test_date_start_default_is_evaluated_per_record(self):
        """The start date default must not be frozen at module load time."""
        default = self.labour_model._fields["date_start"].default
        self.assertTrue(
            callable(default),
            "The start date default must be evaluated for each new record",
        )
        self.assertEqual(
            default(), date.today(), "The default start date is today's date"
        )
