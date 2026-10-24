# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo import fields, models
from odoo.exceptions import MissingError, UserError

REST_DAY_SELECTION = [
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
    ("Sunday", "Sunday"),
]

REST_DAY_REFERENCES = {
    "Monday": "resource_schedule.wd_mon",
    "Tuesday": "resource_schedule.wd_tue",
    "Wednesday": "resource_schedule.wd_wed",
    "Thursday": "resource_schedule.wd_thu",
    "Friday": "resource_schedule.wd_fri",
    "Saturday": "resource_schedule.wd_sat",
    "Sunday": "resource_schedule.wd_sun",
}

# The imported education levels are mapped onto the employee's certificate
# levels. ``hr.employee.certificate`` has no "diploma" value, so a diploma is
# recorded as "other" rather than being dropped.
EDUCATION_CERTIFICATES = {
    "Diploma": "other",
    "BA Degree": "bachelor",
    "Masters Degree": "master",
}

EDUCATION_LEVELS = [str(n) for n in range(1, 13)]


class ImportEmployee(models.Model):
    _name = "hr.data.import.employee"
    _description = "HR Import: Employee"

    name = fields.Char(required=True)
    birthday = fields.Date(groups="hr.group_hr_user", string="Date of Birth")
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")],
        groups="hr.group_hr_user",
    )
    marital = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("cohabitant", "Legal Cohabitant"),
            ("widower", "Widower"),
            ("divorced", "Divorced"),
        ],
        string="Marital Status",
        groups="hr.group_hr_user",
        default="single",
    )
    identification_id = fields.Char(
        string="Identification No", groups="hr.group_hr_user"
    )
    taxid = fields.Char(string="Tax ID")
    place_of_birth = fields.Char()
    education_level = fields.Selection(
        [(level, level) for level in EDUCATION_LEVELS]
        + [
            ("Diploma", "Diploma"),
            ("BA Degree", "BA Degree"),
            ("Masters Degree", "MA Degree"),
        ]
    )
    street = fields.Char(string="Address", groups="hr.group_hr_user")
    private_phone = fields.Char(groups="hr.group_hr_user")
    private_email = fields.Char(groups="hr.group_hr_user")
    emergency_contact = fields.Char(groups="hr.group_hr_user")
    emergency_phone = fields.Char(groups="hr.group_hr_user")
    hire_date = fields.Date(string="Date Hired", help="Initial date of employment.")
    department_id = fields.Many2one("hr.department")
    job_id = fields.Many2one("hr.job", string="Job Position")
    date_start = fields.Date(
        "Start Date", required=True, help="Start date of the contract."
    )
    date_end = fields.Date(
        "End Date", help="End date of the contract (if it's a fixed-term contract)."
    )
    trial_date_end = fields.Date(
        "End of Trial Period", help="End date of the trial period (if there is one)."
    )
    resource_calendar_id = fields.Many2one("resource.calendar", "Working Schedule")
    wage = fields.Monetary(required=True, help="Employee's monthly gross wage.")
    contract_type_id = fields.Many2one("hr.contract.type")
    struct_id = fields.Many2one("hr.payroll.structure", required=True)
    pps_id = fields.Many2one(
        "hr.payroll.period.schedule", "Payroll Period Schedule", required=True
    )
    policy_group_id = fields.Many2one(
        comodel_name="hr.policy.group",
    )
    related_employee_id = fields.Many2one("hr.employee")
    state = fields.Selection(
        [("new", "New"), ("imported", "Imported"), ("updated", "Updated")],
        default="new",
    )
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company)
    currency_id = fields.Many2one(
        string="Currency", related="company_id.currency_id", readonly=True
    )
    DA_LEAVE = "Product Price"
    anlv_earned = fields.Float("Earned", digits=DA_LEAVE, default=0.00)
    anlv_used = fields.Float("Used", digits=DA_LEAVE, default=0.00)
    anlv_remain = fields.Float("Remaining", digits=DA_LEAVE, default=0.00)
    anlv_date = fields.Date("As of")
    rest_day = fields.Selection(selection=REST_DAY_SELECTION)
    # The rest day this module last applied to the employee's schedule, so an
    # update can replace it instead of piling another day off on top of it.
    last_rest_day = fields.Selection(
        selection=REST_DAY_SELECTION, readonly=True, copy=False
    )

    def action_import_employees(self):
        if self.filtered(lambda so: so.state != "new"):
            raise UserError(self.env._("Only new records can be imported."))
        self.import_records()
        self.write({"state": "imported"})

    def action_update_employees(self):
        self.update_records()
        self.write({"state": "updated"})

    def import_records(self):
        partner_obj = self.env["res.partner"]
        country = self.env.ref("base.et")

        values_list = []
        for rec in self:
            company = rec.company_id or self.env.company
            rec = rec.with_company(company)
            # Create contact
            contact = (
                partner_obj.with_company(company)
                .with_context(default_company_id=company.id)
                .create(
                    {
                        "name": rec.name,
                        "street": (rec.street) and rec.street or False,
                        "phone": (rec.private_phone) and rec.private_phone or False,
                        "email": (rec.private_email) and rec.private_email or False,
                        "vat": (rec.taxid) and rec.taxid or False,
                        "company_id": company.id,
                    }
                )
            )

            # Create the basic hr.employee record
            val = {
                "name": rec.name,
                "import_data_id": rec.id,
                "work_contact_id": contact.id,
                "birthday": rec.birthday,
                "place_of_birth": rec.place_of_birth,
                # Odoo 19 replaced the employee ``gender`` field with ``sex``
                # (it lives on ``hr.version``).
                "sex": rec.gender,
                "marital": rec.marital,
                "identification_id": rec.identification_id,
                "private_email": rec.private_email,
                "emergency_contact": rec.emergency_contact,
                "emergency_phone": rec.emergency_phone,
                "hire_date": rec.hire_date,
                "country_id": country.id,
                "country_of_birth": country.id,
                "company_id": company.id,
            }
            if rec.education_level in EDUCATION_LEVELS:
                val.update({"study_field": rec.education_level})
            elif rec.education_level in EDUCATION_CERTIFICATES:
                val.update({"certificate": EDUCATION_CERTIFICATES[rec.education_level]})
            values_list.append((company, val))

        employees = self.env["hr.employee"]
        for company, val in values_list:
            employees |= self.env["hr.employee"].with_company(company).create(val)

        # Link the created employee to the import data record
        for rec in self:
            rec.related_employee_id = employees.filtered(
                lambda e, rec=rec: e.import_data_id.id == rec.id
            )

        # Additional changes to system
        self.create_contracts(employees)
        self.create_annual_leave_allocation(employees)
        self.set_rest_day(employees)

        return employees

    def update_records(self):
        employees = self.env["hr.employee"].search(
            [("id", "in", self.mapped("related_employee_id.id"))]
        )

        # Additional changes to system
        self.set_rest_day(employees)

        return employees

    def create_contracts(self, employee_ids):
        """Write the imported contract data on the employee's ``hr.version``.

        In Odoo 19 ``hr_contract`` was merged into ``hr``: a contract is an
        ``hr.version`` record. A newly created employee already owns one
        version dated today, so the imported contract is written on that
        version and the version is pinned to the imported start date (the
        ``(employee_id, date_version)`` pair is unique).
        """
        for ee in employee_ids:
            data_id = self.filtered(lambda s, ee=ee: s.related_employee_id.id == ee.id)
            if not data_id:
                continue
            version = (
                ee.version_ids.filtered(
                    lambda v, start=data_id.date_start: v.date_version == start
                )
                or ee.version_ids[:1]
            )
            if not version:
                continue

            records = {
                "date_version": data_id.date_start,
                "contract_date_start": data_id.date_start,
                "contract_date_end": data_id.date_end or False,
                "wage": data_id.wage,
                "job_id": data_id.job_id.id,
                "struct_id": data_id.struct_id.id,
                "pps_id": data_id.pps_id.id,
                "policy_group_id": data_id.policy_group_id.id,
            }
            if data_id.trial_date_end and (
                data_id.date_start >= (data_id.trial_date_end - timedelta(days=90))
            ):
                records.update({"trial_date_end": data_id.trial_date_end})
            if data_id.resource_calendar_id:
                records.update(
                    {"resource_calendar_id": data_id.resource_calendar_id.id}
                )
            if data_id.contract_type_id:
                records.update({"contract_type_id": data_id.contract_type_id.id})
            version.write(records)

            # ``department_id`` is computed from the job, so it is written
            # afterwards: the imported department wins and the job's
            # department is only used as a fallback.
            department = data_id.department_id or data_id.job_id.department_id
            if department:
                version.write({"department_id": department.id})
                ee.write({"department_id": department.id})

    def create_annual_leave_allocation(self, employees):
        records = []
        for ee in employees:
            data = self.filtered(lambda s, ee=ee: s.related_employee_id.id == ee.id)
            if not data:
                continue
            anlv_allocation = data.anlv_earned - data.anlv_used
            if anlv_allocation > 0:
                leave_allocation = {
                    "employee_id": ee.id,
                    "name": f"Leave allocation for {data.name} as of {date.today()}",  # noqa: DTZ011
                    "state": "confirm",
                    "number_of_days": anlv_allocation,
                }
                records.append(leave_allocation)

        # Nothing to allocate: the leave type is irrelevant, so do not fail
        # an import that carries no leave balance because of its name.
        if len(records) == 0:
            return

        leave_types = self.env["hr.leave.type"].search([("name", "=", "Annual Leave")])
        if len(leave_types) == 0:
            raise MissingError(
                self.env._("'hr.leave.type' with name 'Annual Leave' not found")
            )
        al_status_id = leave_types[0].id
        for leave_allocation in records:
            leave_allocation["holiday_status_id"] = al_status_id

        leaves = self.env["hr.leave.allocation"].create(records)
        leaves.action_approve()
        # Two-step validation types stop at "validate1" after the first approval
        leaves.filtered(lambda a: a.state == "validate1")._action_validate()

    def get_leave_days_accrued(self, employee, hire_date):
        today = date.today()  # noqa: DTZ011
        accrued_todate = 0
        extra_accrued = 0
        one_day = 0
        tmp_date = hire_date + timedelta(weeks=52, days=1)
        while today >= tmp_date:
            accrued_todate += 20 + extra_accrued + one_day
            tmp_date += timedelta(weeks=52)
            one_day = 1
            extra_accrued += one_day
        if tmp_date > today:
            tmp_date -= timedelta(weeks=52)
            extra_accrued -= one_day
        monthly_accrual = (20 + extra_accrued) / 12.0
        delta = today - tmp_date
        if delta.days > 0:
            accrued_todate += (delta.days / 30) * monthly_accrual

        return accrued_todate

    def _get_rest_day_reference(self, day):
        return self.env.ref(REST_DAY_REFERENCES[day])

    def set_rest_day(self, employees):
        for ee in employees:
            data_id = self.filtered(lambda s, ee=ee: s.related_employee_id.id == ee.id)
            if len(data_id) != 1:
                continue
            resource = ee.resource_id
            previous_day = data_id.last_rest_day
            new_day = data_id.rest_day

            commands = []
            # Replace the day this module imported before, leaving any other
            # day off (for example one set by hand) untouched.
            if previous_day and previous_day != new_day:
                previous_ref = self._get_rest_day_reference(previous_day)
                if previous_ref in resource.dayoff_ids:
                    commands.append((3, previous_ref.id))
            if new_day:
                new_ref = self._get_rest_day_reference(new_day)
                if new_ref not in resource.dayoff_ids:
                    commands.append((4, new_ref.id))
            if commands:
                resource.dayoff_ids = commands
            if data_id.last_rest_day != new_day:
                data_id.last_rest_day = new_day
