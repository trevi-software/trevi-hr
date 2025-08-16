# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


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
        [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("Diploma", "Diploma"),
            ("BA Degree", "BA Degree"),
            ("Masters Degree", "MA Degree"),
        ]
    )
    street = fields.Char(string="Address", groups="hr.group_hr_user")
    private_phone = fields.Char(string="Private Phone", groups="hr.group_hr_user")
    private_email = fields.Char(string="Private Email", groups="hr.group_hr_user")
    emergency_contact = fields.Char("Emergency Contact", groups="hr.group_hr_user")
    emergency_phone = fields.Char("Emergency Phone", groups="hr.group_hr_user")
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
    wage = fields.Monetary("Wage", required=True, help="Employee's monthly gross wage.")
    contract_type_id = fields.Many2one("hr.contract.type", "Contract Type")
    struct_id = fields.Many2one(
        "hr.payroll.structure", string="Salary Structure", required=True
    )
    pps_id = fields.Many2one(
        "hr.payroll.period.schedule", "Payroll Period Schedule", required=True
    )
    policy_group_id = fields.Many2one(
        string="Policy Group",
        comodel_name="hr.policy.group",
    )
    related_employee_id = fields.Many2one("hr.employee")
    state = fields.Selection([("new", "New"), ("imported", "Imported")], default="new")
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company)
    currency_id = fields.Many2one(
        string="Currency", related="company_id.currency_id", readonly=True
    )
    DA_LEAVE = "Product Price"
    anlv_earned = fields.Float("Earned", digits=DA_LEAVE, default=0.00)
    anlv_used = fields.Float("Used", digits=DA_LEAVE, default=0.00)
    anlv_remain = fields.Float("Remaining", digits=DA_LEAVE, default=0.00)
    anlv_date = fields.Date("As of")

    def action_import_employees(self):
        if self.filtered(lambda so: so.state != "new"):
            raise UserError(_("Only new records can be imported."))
        self.import_records()
        self.write({"state": "imported"})

    def import_records(self):

        partner_obj = self.env["res.partner"]

        # Create the basic hr.employee record
        values_list = []
        for rec in self:
            # Create contact
            contact = partner_obj.create(
                {
                    "name": rec.name,
                    "type": "private",
                    "street": (rec.street) and rec.street or False,
                    "mobile": (rec.private_phone) and rec.private_phone or False,
                    "email": (rec.private_email) and rec.private_email or False,
                    "vat": (rec.taxid) and rec.taxid or False,
                }
            )
            val = {
                "name": rec.name,
                "import_data_id": rec.id,
                "address_home_id": contact.id,
                "birthday": rec.birthday,
                "place_of_birth": rec.place_of_birth,
                "gender": rec.gender,
                "marital": rec.marital,
                "identification_id": rec.identification_id,
                "private_email": rec.private_email,
                "emergency_contact": rec.emergency_contact,
                "emergency_phone": rec.emergency_phone,
                "hire_date": rec.hire_date,
            }
            if rec.education_level in [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
            ]:
                val.update({"study_field": rec.education_level})
            elif rec.education_level == "diploma":
                val.update({"certificate": "diploma"})
            elif rec.education_level == "ba":
                val.update({"certificate": "bachelor"})
            values_list.append(val)

        employees = self.env["hr.employee"].create(values_list)

        # Link the created employee to the import data record
        for rec in self:
            rec.related_employee_id = employees.filtered(
                lambda e, rec=rec: e.import_data_id.id == rec.id
            )

        # Additional changes to system
        self.create_contracts(employees)
        self.create_annual_leave_allocation(employees)

        return employees

    def create_contracts(self, employee_ids):
        contracts_list = []
        for ee in employee_ids:
            data_id = self.filtered(lambda s, ee=ee: s.related_employee_id.id == ee.id)
            records = {
                "employee_id": ee.id,
                "wage": data_id.wage,
                "date_start": data_id.date_start,
                "job_id": data_id.job_id.id,
                "struct_id": data_id.struct_id.id,
                "pps_id": data_id.pps_id.id,
                "policy_group_id": data_id.policy_group_id.id,
                "kanban_state": "done",
            }
            if data_id.date_end:
                records.update({"date_end": data_id.date_end})
            if data_id.trial_date_end:
                records.update({"trial_date_end": data_id.trial_date_end})
            if data_id.resource_calendar_id:
                records.update(
                    {"resource_calendar_id": data_id.resource_calendar_id.id}
                )
            if data_id.contract_type_id:
                records.update({"contract_type_id": data_id.contract_type_id.id})
            contracts_list.append(records)

        self.env["hr.contract"].create(contracts_list) \
                               .signal_confirm()

    def create_annual_leave_allocation(self, employees):
        al_status_id = (
            self.env["hr.leave.type"].search([("name", "=", "Annual Leave")])[0].id
        )
        records = {}
        for ee in employees:
            data = self.filtered(lambda s, ee=ee: s.related_employee_id.id == ee.id)
            anlv_allocation = data.anlv_earned - data.anlv_used
            if anlv_allocation > 0:
                leave_allocation = {
                    "employee_id": ee.id,
                    "name": "Leave allocation for {} as of {}".format(
                        data.name, date.today()
                    ),
                    "state": "draft",
                    "holiday_status_id": al_status_id,
                    "number_of_days": data.anlv_earned - data.anlv_used,
                }
                records.append(leave_allocation)

        if len(records) > 0:
            self.env["hr.leave.allocation"].create(records)  \
                                           .action_confirm() \
                                           .action_approve()

    def get_leave_days_accrued(self, employee, hire_date):

        today = date.today()
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
