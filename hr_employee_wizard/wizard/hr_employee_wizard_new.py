# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo import _, api, exceptions, fields, models


class NewLabour(models.TransientModel):

    _name = "hr.employee.wizard.new"
    _description = "New Employee Wizard"

    @api.model
    def _get_wage(self):

        Contract = self.env["hr.contract"].with_company(self.env.company)
        return Contract._get_wage()

    @api.model
    def _get_trial_start(self):

        Contract = self.env["hr.contract"].with_company(self.env.company)
        return Contract._get_trial_date_start()

    @api.model
    def _get_trial_end(self):

        Contract = self.env["hr.contract"].with_company(self.env.company)
        return Contract._get_trial_date_end()

    @api.model
    def _get_struct(self):

        Contract = self.env["hr.contract"].with_company(self.env.company)
        return Contract._get_struct()

    @api.model
    def _get_policy_group(self):

        Contract = self.env["hr.contract"].with_company(self.env.company)
        return Contract._get_policy_group()

    @api.model
    def _get_resource_calendar(self):

        Contract = self.env["hr.contract"].with_company(self.env.company)
        return Contract._get_resource_calendar()

    @api.model
    def _get_pps(self):

        Contract = self.env["hr.contract"].with_company(self.env.company)
        return Contract._get_pay_sched()

    employee_ids = fields.Many2many(
        string="Employees",
        comodel_name="hr.employee",
    )
    new_benefit_ids = fields.One2many(
        string="New Benefits",
        comodel_name="hr.employee.wizard.benefit",
        inverse_name="wizard_id",
    )
    state = fields.Selection(
        selection=[
            ("personal", "Personal"),
            ("contract", "Contract"),
            ("benefits", "Benefits"),
            ("review", "Review"),
        ],
        default="personal",
        readonly=True,
        string="Status",
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda s: s.env.company,
        required=True,
    )

    # Personal Details
    #
    name = fields.Char()
    birth_date = fields.Date()
    gender = fields.Selection(selection=[("f", "Female"), ("m", "Male")])
    id_no = fields.Char(string="Official ID")
    street = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one(comodel_name="res.country.state", string="State")
    country_id = fields.Many2one(
        comodel_name="res.country",
        string="Country",
        default=lambda s: s.env.company.country_id,
    )
    telephone = fields.Char()
    mobile = fields.Char()
    education = fields.Selection(
        selection=[
            ("graduate", "Graduate"),
            ("bachelor", "Bachelor"),
            ("master", "Master"),
            ("doctor", "Doctor"),
            ("other", "Other"),
        ],
        default="other",
    )

    # Contract Details
    #
    job_id = fields.Many2one(comodel_name="hr.job", string="Applied Job")
    department_id = fields.Many2one(comodel_name="hr.department", string="Department")
    struct_id = fields.Many2one(
        string="Salary Structure",
        comodel_name="hr.payroll.structure",
        default=_get_struct,
    )
    pps_id = fields.Many2one(
        string="Payroll Period Schedule",
        comodel_name="hr.payroll.period.schedule",
        default=_get_pps,
    )
    policy_group_id = fields.Many2one(
        string="Policy Group", comodel_name="hr.policy.group", default=_get_policy_group
    )
    wage = fields.Float(
        digits="Payroll", default=_get_wage, help="Basic Salary of the employee"
    )
    calendar_id = fields.Many2one(
        string="Working Schedule Template",
        comodel_name="resource.calendar",
        default=_get_resource_calendar,
    )
    date_start = fields.Date(string="Start Date", default=fields.Date.today())
    date_end = fields.Date(string="End Date")
    trial_date_start = fields.Date(string="Trial Start Date", default=_get_trial_start)
    trial_date_end = fields.Date(string="Trial End Date", default=_get_trial_end)

    @api.onchange("company_id")
    def onchange_company(self):

        for rec in self:
            if not self.company_id:
                continue

            Contract = self.env["hr.contract"].with_company(self.company_id)
            rec.wage = Contract._get_wage()
            rec.struct_id = Contract._get_struct()
            rec.trial_date_start = Contract._get_trial_date_start()
            rec.trial_date_end = Contract._get_trial_date_end()
            rec.calendar_id = Contract._get_resource_calendar()
            rec.pps_id = Contract._get_pay_sched()
            rec.policy_group_id = Contract._get_policy_group()

    @api.onchange("job_id")
    def onchange_job(self):

        for rec in self:

            if not rec.job_id:
                rec.department_id = False
                rec.wage = False
                continue
            Contract = self.env["hr.contract"].with_company(rec.company_id)
            rec.department_id = rec.job_id.department_id
            rec.wage = Contract._get_wage(job_id=self.job_id.id)

    @api.onchange("date_start")
    def onchange_date(self):

        for rec in self:
            if rec.date_start:
                rec.trial_date_start = rec.date_start
            else:
                rec.trial_date_start = date.today()
            rec.onchange_trial()

    @api.onchange("trial_date_start")
    def onchange_trial(self):

        for rec in self:
            Contract = self.env["hr.contract"].with_company(rec.company_id)
            if rec.trial_date_start:
                dStart = self.trial_date_start
                rec.trial_date_end = Contract._get_trial_date_end_from_start(dStart)

    @api.onchange("country_id")
    def onchange_country(self):

        res = {"domain": {"state_id": False}}
        if self.country_id:
            res["domain"]["state_id"] = [("country_id", "=", self.country_id.id)]

        return res

    def create_partner(self):

        self.ensure_one()
        values = {
            "type": "private",
            "name": self.name,
            "phone": self.telephone,
            "mobile": self.mobile,
            "street": self.street,
            "city": self.city,
            "country_id": self.country_id.id,
            "state_id": self.state_id and self.state_id.id or False,
            "employee": True,
            "is_company": False,
            "company_id": self.company_id.id,
        }

        return self.env["res.partner"].create(values)

    def _create_hr_applicant(self, partner):

        self.ensure_one()
        applicant_vals = {
            "name": f"{self.job_id.name} {self.name}",
            "partner_name": self.name,
            "partner_id": partner.id,
            "partner_phone": self.telephone,
            "partner_mobile": self.mobile,
            "job_id": self.job_id.id,
            "department_id": self.department_id.id,
            "gender": self.gender,
            "birth_date": self.birth_date,
            "education": self.education,
        }
        return self.env["hr.applicant"].create(applicant_vals)

    def create_applicant(self):

        self.ensure_one()
        if not self.name or not self.birth_date or not self.gender:
            raise exceptions.ValidationError(
                _(
                    "Mandatory Fields Missing "
                    "Make sure that at least the Name, Birth Date and Gender "
                    "fields have been filled in."
                )
            )

        # Create partner
        partner = self.create_partner()

        # Create applicant
        applicant = self._create_hr_applicant(partner)

        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.employee.wizard.new",
            "res_id": applicant.id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": self.env.context,
        }

    def hire_applicant(self):

        if not self.name or not self.birth_date or not self.gender:
            raise exceptions.ValidationError(
                _(
                    "Mandatory Fields Missing "
                    "Make sure that at least the Name, Birth Date and Gender "
                    "fields have been filled in."
                )
            )

        # Create partner
        partner_id = self.create_partner()

        # Create applicant
        applicant = self._create_hr_applicant(partner_id)

        # Set the applicant's stage to 'Contract Signed'
        stage = self.env.ref("hr_recruitment.stage_job5")
        if stage:
            applicant.stage_id = stage.id

        # Create employee
        dict_act_window = applicant.create_employee_from_applicant()
        employee_values = {
            "name": dict_act_window["context"]["default_name"],
            "job_id": dict_act_window["context"]["default_job_id"],
            "job_title": dict_act_window["context"]["default_job_title"],
            "address_home_id": dict_act_window["context"]["default_address_home_id"],
            "department_id": dict_act_window["context"]["default_department_id"],
            "address_id": dict_act_window["context"]["default_address_id"],
            "work_email": dict_act_window["context"]["default_work_email"],
            "work_phone": dict_act_window["context"]["default_work_phone"],
            "applicant_id": dict_act_window["context"]["default_applicant_id"],
        }
        ee = self.env["hr.employee"].create(employee_values)

        # Create contract
        #
        c_vals = {
            "employee_id": ee.id,
            "job_id": self.job_id.id,
            "department_id": self.department_id.id,
            "wage": self.wage,
            "struct_id": self.struct_id.id,
            "policy_group_id": self.policy_group_id.id,
            "date_start": self.date_start,
            "date_end": self.date_end,
            "trial_date_start": self.trial_date_start,
            "trial_date_end": self.trial_date_end,
            "resource_calendar_id": self.calendar_id.id,
            "pps_id": self.pps_id.id,
        }
        self.env["hr.contract"].create(c_vals)

        # Enroll in benefits
        #
        BenefitPolicy = self.env["hr.benefit.policy"]
        for newb in self.new_benefit_ids:
            newb_vals = {
                "employee_id": ee.id,
                "benefit_id": newb.benefit_id.id,
                "benefit_code": newb.benefit_id.code,
                "start_date": newb.effective_date,
                "end_date": newb.end_date,
                "advantage_override": newb.adv_override,
                "premium_override": newb.prm_override,
                "advantage_amount": newb.adv_amount,
                "premium_amount": newb.prm_amount,
                "premium_total": newb.prm_total,
            }
            BenefitPolicy.create(newb_vals)

        # Add employee ID to list of hired employees
        if self.env.context.get("new_employee_ids", False):
            ctx = dict(self.env.context)
            ctx["new_employee_ids"].append(ee.id)
        else:
            ctx = dict(self.env.context)
            ctx.update({"new_employee_ids": [ee.id]})

        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.employee.wizard.new",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": ctx,
        }

    def cancel_wizard(self):

        action = self.env.ref("hr.open_view_employee_list_my")
        dict_act_window = action.read([])[0]
        dict_act_window["view_mode"] = "kanban,tree,form"
        dict_act_window["domain"] = [
            ("id", "in", self.env.context.get("new_employee_ids", False))
        ]
        self.env.context.get("new_employee_ids", False)
        return dict_act_window

    def state_contract(self):

        self.ensure_one()
        self.state = "contract"
        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.employee.wizard.new",
            "res_id": self.ids[0],
            "type": "ir.actions.act_window",
            "target": "new",
            "nodestroy": True,
            "context": self.env.context,
        }

    def state_benefits(self):

        self.ensure_one()
        self.state = "benefits"
        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.employee.wizard.new",
            "res_id": self.ids[0],
            "type": "ir.actions.act_window",
            "target": "new",
            "nodestroy": True,
            "context": self.env.context,
        }

    def state_review(self):

        self.ensure_one()
        self.state = "review"
        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.employee.wizard.new",
            "res_id": self.ids[0],
            "type": "ir.actions.act_window",
            "target": "new",
            "nodestroy": True,
            "context": self.env.context,
        }
