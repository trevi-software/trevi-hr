# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo import api, exceptions, fields, models


class NewLabour(models.TransientModel):
    _name = "hr.employee.wizard.new"
    _description = "New Employee Wizard"

    @api.model
    def _get_wage(self):
        Contract = self.env["hr.version"].with_company(self.env.company)
        return Contract._get_wage()

    @api.model
    def _get_trial_start(self):
        Contract = self.env["hr.version"].with_company(self.env.company)
        return Contract._get_trial_date_start()

    @api.model
    def _get_trial_end(self):
        Contract = self.env["hr.version"].with_company(self.env.company)
        return Contract._get_trial_date_end()

    @api.model
    def _get_struct(self):
        Contract = self.env["hr.version"].with_company(self.env.company)
        return Contract._get_struct()

    @api.model
    def _get_policy_group(self):
        Contract = self.env["hr.version"].with_company(self.env.company)
        return Contract._get_policy_group()

    @api.model
    def _get_resource_calendar(self):
        Contract = self.env["hr.version"].with_company(self.env.company)
        return Contract._get_resource_calendar()

    @api.model
    def _get_pps(self):
        Contract = self.env["hr.version"].with_company(self.env.company)
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
    state_id = fields.Many2one(comodel_name="res.country.state")
    country_id = fields.Many2one(
        comodel_name="res.country",
        default=lambda s: s.env.company.country_id,
    )
    telephone = fields.Char()
    mobile = fields.Char()
    education = fields.Selection(
        selection=[
            ("graduate", "High School"),
            ("diploma", "Diploma"),
            ("bachelor", "Bachelor (BA)"),
            ("master", "Master (MA)"),
            ("doctor", "Doctorate"),
            ("other", "Other"),
        ],
        default="other",
    )

    # Contract Details
    #
    job_id = fields.Many2one(comodel_name="hr.job", string="Applied Job")
    department_id = fields.Many2one(comodel_name="hr.department")
    struct_id = fields.Many2one(
        string="Salary Structure",
        comodel_name="hr.payroll.structure",
        default=lambda self: self._get_struct(),
    )
    pps_id = fields.Many2one(
        string="Payroll Period Schedule",
        comodel_name="hr.payroll.period.schedule",
        default=lambda self: self._get_pps(),
    )
    policy_group_id = fields.Many2one(
        comodel_name="hr.policy.group", default=lambda self: self._get_policy_group()
    )
    wage = fields.Float(
        digits="Payroll",
        default=lambda self: self._get_wage(),
        help="Basic Salary of the employee",
    )
    calendar_id = fields.Many2one(
        string="Working Schedule Template",
        comodel_name="resource.calendar",
        default=lambda self: self._get_resource_calendar(),
    )
    date_start = fields.Date(string="Start Date", default=fields.Date.today)
    date_end = fields.Date(string="End Date")
    trial_date_start = fields.Date(
        string="Trial Start Date", default=lambda self: self._get_trial_start()
    )
    trial_date_end = fields.Date(
        string="Trial End Date", default=lambda self: self._get_trial_end()
    )

    @api.onchange("company_id")
    def onchange_company(self):
        for rec in self:
            if not self.company_id:
                continue

            contract = self.env["hr.version"].with_company(self.company_id)
            rec.wage = contract._get_wage()
            rec.struct_id = contract._get_struct()
            rec.trial_date_start = contract._get_trial_date_start()
            rec.trial_date_end = contract._get_trial_date_end()
            rec.calendar_id = contract._get_resource_calendar()
            rec.pps_id = contract._get_pay_sched()
            rec.policy_group_id = contract._get_policy_group()

    @api.onchange("job_id")
    def onchange_job(self):
        for rec in self:
            if not rec.job_id:
                rec.department_id = False
                rec.wage = False
                continue
            contract = self.env["hr.version"].with_company(rec.company_id)
            rec.department_id = rec.job_id.department_id
            rec.wage = contract._get_wage(job_id=self.job_id.id)

    @api.onchange("date_start")
    def onchange_date(self):
        for rec in self:
            if rec.date_start:
                rec.trial_date_start = rec.date_start
            else:
                rec.trial_date_start = date.today()  # noqa: DTZ011
            rec.onchange_trial()

    @api.onchange("trial_date_start")
    def onchange_trial(self):
        for rec in self:
            contract = self.env["hr.version"].with_company(rec.company_id)
            if rec.trial_date_start:
                d_start = self.trial_date_start
                rec.trial_date_end = contract._get_trial_date_end_from_start(d_start)

    @api.onchange("country_id")
    def onchange_country(self):
        res = {"domain": {"state_id": False}}
        if self.country_id:
            res["domain"]["state_id"] = [("country_id", "=", self.country_id.id)]

        return res

    def create_partner(self):
        self.ensure_one()
        values = {
            "name": self.name,
            # Odoo 19 merged ``mobile`` into ``phone`` on res.partner.
            "phone": self.mobile or self.telephone,
            "street": self.street,
            "city": self.city,
            "country_id": self.country_id.id,
            "state_id": self.state_id and self.state_id.id or False,
            "is_company": False,
            "company_id": self.company_id.id,
        }

        return self.env["res.partner"].create(values)

    def _create_hr_applicant(self, partner):
        self.ensure_one()
        applicant_vals = {
            "partner_name": self.name,
            "partner_id": partner.id,
            "partner_phone": self.telephone,
            "company_id": self.company_id.id,
            "job_id": self.job_id.id,
            "department_id": self.department_id.id,
            "gender": self.gender,
            "birth_date": self.birth_date,
            "education": self.education,
            "id_no": self.id_no,
        }
        return self.env["hr.applicant"].create(applicant_vals)

    def create_applicant(self):
        self.ensure_one()
        if not self.name or not self.birth_date or not self.gender:
            raise exceptions.ValidationError(
                self.env._(
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
            "view_mode": "form",
            "res_model": "hr.applicant",
            "res_id": applicant.id,
            "type": "ir.actions.act_window",
            "target": "current",
            "context": self.env.context,
        }

    def hire_applicant(self):
        if not self.name or not self.birth_date or not self.gender:
            raise exceptions.ValidationError(
                self.env._(
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
        ee = self.env["hr.employee"].browse(dict_act_window["res_id"])

        # Create the contract.  In Odoo 19 ``hr_contract`` was merged into
        # ``hr``: a contract is an ``hr.version`` record, its dates live in
        # ``contract_date_start``/``contract_date_end`` and every employee
        # already owns a version dated today.
        #
        Version = self.env["hr.version"].with_company(self.company_id)
        c_vals = {
            "employee_id": ee.id,
            "job_id": self.job_id.id,
            "department_id": self.department_id.id,
            "wage": self.wage,
            "struct_id": self.struct_id.id,
            "policy_group_id": self.policy_group_id.id,
            "contract_date_start": self.date_start,
            "contract_date_end": self.date_end,
            "trial_date_start": self.trial_date_start,
            "trial_date_end": self.trial_date_end,
            "resource_calendar_id": self.calendar_id.id,
            "pps_id": self.pps_id.id,
        }
        version = ee.version_ids.filtered(
            lambda v, d=self.date_start: v.date_version == d
        )
        if not version:
            # The employee was given an initial version dated today, without
            # any contract details, when it was created. Reuse that version so
            # the wizard's values end up on the employee's only version:
            # ``hr.version`` backdates it when it is the employee's sole
            # version, whereas a second, populated version would leave the
            # empty one behind as ``current_version_id`` for a past hire.
            version = ee.version_ids.filtered(lambda v: not v.contract_date_start)
        if version:
            # (employee_id, date_version) is unique: reuse the version that is
            # already pinned to this start date instead of creating a second one.
            version.write(c_vals)
            # ``resource_schedule`` builds the first-hire shifts from
            # ``hr.version.create()`` only, and that version was created before
            # it carried a contract date. Run that step now that it has one.
            self._create_first_hire_schedule(ee)
        else:
            c_vals["date_version"] = self.date_start
            Version.create(c_vals)

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
            "view_mode": "form",
            "res_model": "hr.employee.wizard.new",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": ctx,
        }

    def _create_first_hire_schedule(self, employee):
        """Schedule the first shifts for an employee hired by the wizard.

        ``resource_schedule`` only creates those shifts from
        ``hr.version.create()``. The version this wizard reuses was created
        before it carried a contract date, so when it becomes the employee's
        first contract the scheduling step has to be run explicitly.
        """
        self.ensure_one()
        contracts = employee.version_ids.filtered("contract_date_start")
        if len(contracts) != 1:
            # Only the first contract of an employee is scheduled; later
            # contracts are scheduled by the mass schedule cron.
            return
        if employee.scheduled_shift_ids:
            # Never duplicate a schedule that already exists.
            return
        today = fields.Date.today()
        d_end_contract = contracts.contract_date_end
        if d_end_contract and d_end_contract < today:
            # The contract is already over: there is nothing to schedule.
            return

        # Schedule up to the next mass schedule, exactly like
        # ``resource_schedule`` does for a first contract.
        d_start = max(contracts.contract_date_start, today)
        d_end = d_start
        # ``ir.cron`` is admin-only, but the next mass schedule date is the
        # only thing read here and it only sizes the range: elevate the read
        # so an HR officer can hire without system administration rights.
        xref = self.env.ref(
            "resource_schedule.mass_schedule_cron", raise_if_not_found=False
        ).sudo()
        if xref and xref.nextcall:
            d_end = fields.Datetime.to_datetime(xref.nextcall).date()
        if d_end < d_start:
            d_end = d_start
        while d_end.weekday() != 6:
            d_end += timedelta(days=1)
        # The schedule starts on the Monday of the week of the hire.
        while d_start.weekday() != 0:
            d_start -= timedelta(days=1)

        # Creating shifts is a scheduling operation: ``resource_schedule``
        # itself elevates only the ``resource.schedule.shift`` model when it
        # builds the first-hire schedule from ``hr.version.create()`` (see
        # ``resource_schedule/models/hr_contract.py``). Hiring must not
        # require ``resource_schedule.group_scheduling_user``, so elevate
        # exactly that call and nothing else: the wizard still reads and
        # writes the employee with the hiring officer's own rights, and the
        # only records created are the employee's own shifts for the period
        # computed above.
        sched_obj = self.env["resource.schedule.shift"]
        sched_obj.sudo().create_schedule(employee.resource_id, d_start, d_end)

    def cancel_wizard(self):
        action = self.env.ref("hr.open_view_employee_list_my")
        dict_act_window = action.read([])[0]
        dict_act_window["view_mode"] = "kanban,list,form"
        dict_act_window["domain"] = [
            ("id", "in", self.env.context.get("new_employee_ids", False))
        ]
        self.env.context.get("new_employee_ids", False)
        return dict_act_window

    def state_contract(self):
        self.ensure_one()
        self.state = "contract"
        return {
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
            "view_mode": "form",
            "res_model": "hr.employee.wizard.new",
            "res_id": self.ids[0],
            "type": "ir.actions.act_window",
            "target": "new",
            "nodestroy": True,
            "context": self.env.context,
        }
