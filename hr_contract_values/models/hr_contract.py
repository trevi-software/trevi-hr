# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from odoo.tools.translate import _


class ContractInit(models.Model):

    _name = "hr.contract.init"
    _description = "Initial Contract Settings"
    _check_company_auto = True
    # Return records with latest date first
    _order = "date desc"

    name = fields.Char(
        string="Name",
        size=64,
        required=True,
    )
    date = fields.Date(
        string="Effective Date",
        required=True,
    )
    wage_ids = fields.One2many(
        comodel_name="hr.contract.init.wage",
        inverse_name="contract_init_id",
        string="Starting Wages",
    )
    trial_period = fields.Integer(
        string="Trial Period",
        default=0,
        help="Length of Trial Period, in days",
    )
    active = fields.Boolean(default=True)
    locked = fields.Boolean()
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
        groups="base.group_multi_company",
    )
    contract_type = fields.Many2one("hr.payroll.structure.type")

    def lock(self):
        for record in self:
            record.locked = True

    def unlock(self):
        for record in self:
            record.locked = False

    def unlink(self):

        for record in self:
            if record.locked:
                raise UserError(
                    _(
                        "You may not delete a record that is locked. You must unlock it first."
                    )
                )
        return super(ContractInit, self).unlink()

    def write(self, vals):
        for record in self:
            if record.locked:
                if "locked" in vals.keys():
                    if vals["locked"] is False:
                        continue
                raise UserError(
                    _(
                        "You may not update a record that is locked. You must unlock it first."
                    )
                )
        return super(ContractInit, self).write(vals)


class HrContract(models.Model):

    _inherit = "hr.contract"

    @api.model
    def _get_wage(self, job_id=None):

        res = 0
        default = 0
        job = False
        init = self.get_latest_initial_values()
        if job_id:
            job = self.env["hr.job"].browse(job_id)
        else:
            job = False
        if init is not None:
            for line in init.wage_ids:
                if job_id is not None and line.job_id.id == job_id:
                    res = line.starting_wage
                elif job:
                    cat_id = False
                    category_ids = [c.id for c in line.category_ids]
                    for ci in job.category_ids.ids:
                        if ci in category_ids:
                            cat_id = ci
                            break
                    if cat_id:
                        res = line.starting_wage
                if line.is_default and default == 0:
                    default = line.starting_wage
                if res != 0:
                    break
        if res == 0:
            res = default
        return res

    @api.model
    def _get_trial_date_start(self):

        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.trial_period and init.trial_period > 0:
            res = datetime.now().strftime(OE_DFORMAT)
        return res

    @api.model
    def _get_trial_date_end(self):

        return self._get_trial_date_end_from_start(datetime.now().date())

    @api.model
    def _get_trial_date_end_from_start(self, dToday):

        res = False
        init = self.get_latest_initial_values()
        if dToday and init is not None and init.trial_period and init.trial_period > 0:
            dEnd = dToday + timedelta(days=(init.trial_period))
            res = dEnd.strftime(OE_DFORMAT)
        return res

    @api.model
    def _get_structure_type(self):

        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.contract_type:
            res = init.contract_type
        return res

    wage = fields.Monetary(default=_get_wage)
    trial_date_start = fields.Date(default=_get_trial_date_start)
    trial_date_end = fields.Date(default=_get_trial_date_end)
    structure_type_id = fields.Many2one(default=_get_structure_type)

    @api.model
    def create(self, vals):

        # set default wage based on the job
        if "wage" not in vals.keys() and "job_id" in vals.keys():
            _wage = self._get_wage(job_id=vals["job_id"])
            if _wage != 0:
                vals.update({"wage": _wage})

        return super(HrContract, self).create(vals)

    @api.onchange("job_id")
    def onchange_job(self):

        for c in self:
            if c.job_id:
                c.wage = self._get_wage(job_id=c.job_id.id)

    @api.onchange("trial_date_start")
    def onchange_trial(self):

        res = {"value": {"trial_date_end": False}}

        init = self.get_latest_initial_values()
        if init is not None and init.trial_period and init.trial_period > 0:
            dStart = datetime.strptime(self.trial_date_start, OE_DFORMAT)
            dEnd = dStart + timedelta(days=(init.trial_period - 1))
            res["value"]["trial_date_end"] = dEnd.strftime(OE_DFORMAT)

        return res

    @api.model
    def get_latest_initial_values(self, today_str=None):
        """Return a record with an effective date before today_str but
        greater than all others"""

        init_obj = self.env["hr.contract.init"]
        if today_str is None:
            today_str = datetime.now().strftime(OE_DFORMAT)
        dToday = datetime.strptime(today_str, OE_DFORMAT).date()
        domain = [("date", "<=", today_str)]
        res = None

        # Get company. If the caller wants to enforce a specific company use
        # that one, otherwise use the company associated with the parent
        # user record, if any.
        #
        if self.env.context.get("force_company", False):
            domain = domain + [("company_id", "=", self.env.context["force_company"])]
        else:
            if self.env.user.company_id:
                domain = domain + [("company_id", "=", self.env.user.company_id.id)]

        # If we can't find records for the employee's company, search for
        # ones without a specific company attached.
        #
        ids = init_obj.search(domain)
        if len(ids) == 0:
            domain = [("date", "<=", today_str), ("company_id", "=", False)]
            ids = init_obj.search(domain)

        for init in ids:
            if init.date <= dToday:
                if res is None:
                    res = init
                elif init.date > res.date:
                    res = init

        return res
