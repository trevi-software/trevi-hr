# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

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
    street = fields.Char(string="Address", groups="hr.group_hr_user")
    private_phone = fields.Char(string="Private Phone", groups="hr.group_hr_user")
    private_email = fields.Char(string="Private Email", groups="hr.group_hr_user")
    emergency_contact = fields.Char("Emergency Contact", groups="hr.group_hr_user")
    emergency_phone = fields.Char("Emergency Phone", groups="hr.group_hr_user")
    hire_date = fields.Date(string="Date Hired", help="Initial date of employment.")
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

    def action_import_employees(self):
        if self.filtered(lambda so: so.state != "new"):
            raise UserError(_("Only new records can be imported."))
        self.import_records()
        self.write({"state": "imported"})

    def import_records(self):

        Partner = self.env["res.partner"]

        # Create the basic hr.employee record
        values_list = []
        for rec in self:
            # Create contact
            _contact = Partner.create(
                {
                    "name": rec.name,
                    "type": "private",
                    "street": rec.street and rec.street or False,
                    "mobile": rec.private_phone and rec.private_phone or False,
                    "email": rec.private_email and rec.private_email or False,
                    "vat": rec.taxid and rec.taxid or False,
                }
            )
            val = {
                "name": rec.name,
                "import_data_id": rec.id,
                "address_home_id": _contact.id,
            }
            if rec.birthday:
                val.update({"birthday": rec.birthday})
            if rec.gender:
                val.update({"gender": rec.gender})
            if rec.marital:
                val.update({"marital": rec.marital})
            if rec.identification_id:
                val.update({"identification_id": rec.identification_id})
            if rec.private_email:
                val.update({"private_email": rec.private_email})
            if rec.emergency_contact:
                val.update({"emergency_contact": rec.emergency_contact})
            if rec.emergency_phone:
                val.update({"emergency_phone": rec.emergency_phone})
            if rec.hire_date:
                val.update({"hire_date": rec.hire_date})
            values_list.append(val)
        res = self.env["hr.employee"].create(values_list)

        # Link the created employee to the import data record
        for rec in self:
            rec.related_employee_id = res.filtered(
                lambda e: e.import_data_id.id == rec.id
            )

        # Additional changes to system
        contracts = self.create_contracts(res)
        contracts.signal_confirm()

        return res

    def create_contracts(self, employee_ids):
        contracts_list = []
        for ee in employee_ids:
            data_id = self.filtered(lambda s: s.related_employee_id.id == ee.id)
            contract_vals = {
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
                contract_vals.update({"date_end": data_id.date_end})
            if data_id.trial_date_end:
                contract_vals.update({"trial_date_end": data_id.trial_date_end})
            if data_id.resource_calendar_id:
                contract_vals.update(
                    {"resource_calendar_id": data_id.resource_calendar_id.id}
                )
            if data_id.contract_type_id:
                contract_vals.update({"contract_type_id": data_id.contract_type_id.id})
            contracts_list.append(contract_vals)
        return self.env["hr.contract"].create(contracts_list)
