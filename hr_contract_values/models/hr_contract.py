# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class ContractInit(models.Model):
    _name = "hr.contract.init"
    _description = "Initial Contract Settings"
    _check_company_auto = True
    # Return records with latest date first
    _order = "date desc"

    name = fields.Char(
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
        default=0,
        help="Length of Trial Period, in days",
    )
    active = fields.Boolean(default=True)
    locked = fields.Boolean()
    company_id = fields.Many2one(
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

    @api.ondelete(at_uninstall=False)
    def _unlink_if_not_locked(self):
        for record in self:
            if record.locked:
                raise UserError(
                    self.env._(
                        "You may not delete a record that is locked. Unlock it first."
                    )
                )

    def write(self, vals):
        for record in self:
            if record.locked and vals.get("locked") is not False:
                raise UserError(
                    self.env._(
                        "You may not update a record that is locked. Unlock it first."
                    )
                )
        return super().write(vals)


class HrVersion(models.Model):
    """Seed a new employee contract from the latest ``hr.contract.init`` record.

    In Odoo 19 ``hr_contract`` was merged into ``hr`` and ``hr.contract`` was
    renamed to ``hr.version``: ``wage``, ``structure_type_id`` and
    ``trial_date_end`` now live there, and the ``hr.employee``'s contract data
    is delegated to its current version through ``_inherits``.
    """

    _inherit = "hr.version"

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
            res = fields.Date.today()
        return res

    @api.model
    def _get_trial_date_end(self):
        return self._get_trial_date_end_from_start(fields.Date.today())

    @api.model
    def _get_trial_date_end_from_start(self, dToday):
        res = False
        init = self.get_latest_initial_values()
        if dToday and init is not None and init.trial_period and init.trial_period > 0:
            dEnd = dToday + timedelta(days=(init.trial_period))
            res = dEnd
        return res

    @api.model
    def _get_structure_type(self):
        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.contract_type:
            res = init.contract_type
        return res

    # ``hr.version`` already declares ``wage``, ``trial_date_end`` and
    # ``structure_type_id`` (with their own groups/tracking/compute), so the
    # Odoo 18 field defaults cannot be re-declared here without losing those
    # attributes.  Their defaults are applied in ``create`` instead, while the
    # ``trial_date_start`` (trevi-specific, absent from core) keeps a real
    # field default.
    trial_date_start = fields.Date(
        string="Start of Trial Period",
        default=lambda self: self._get_trial_date_start(),
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # pre-fill the wage from the initial values of the job, if any
            if "wage" not in vals:
                _wage = self._get_wage(job_id=vals.get("job_id"))
                if _wage != 0:
                    vals["wage"] = _wage
            if "trial_date_end" not in vals:
                _trial_date_end = self._get_trial_date_end()
                if _trial_date_end:
                    vals["trial_date_end"] = _trial_date_end
            if "structure_type_id" not in vals:
                _structure_type = self._get_structure_type()
                if _structure_type:
                    vals["structure_type_id"] = _structure_type.id

        return super().create(vals_list)

    @api.onchange("job_id")
    def onchange_job(self):
        for version in self:
            if version.job_id:
                version.wage = self._get_wage(job_id=version.job_id.id)

    @api.onchange("trial_date_start")
    def onchange_trial(self):
        self.trial_date_end = False

        init = self.get_latest_initial_values()
        if init is not None and init.trial_period and init.trial_period > 0:
            dStart = self.trial_date_start
            dEnd = dStart + timedelta(days=(init.trial_period - 1))
            self.trial_date_end = dEnd

    @api.model
    def get_latest_initial_values(self, today_str=None):
        """Return a record with an effective date before today_str but
        greater than all others"""

        init_obj = self.env["hr.contract.init"].sudo()
        if today_str is None:
            today_str = fields.Date.today()
        dToday = fields.Date.to_date(today_str)
        domain = [("date", "<=", today_str)]
        res = None

        # Restrict the search to the company in the environment.
        #
        # Use the company the caller is working in.  ``self.env.company`` is set
        # by ``with_company()``, which Odoo refuses for a company the user may
        # not access; that matters here because the ``sudo()`` search below is
        # not subject to the multi-company record rule.  Reading the deprecated
        # ``force_company`` context key instead would let a caller reach another
        # company's initial values (default starting wage, trial period, ...).
        #
        company = self.env.company
        if company:
            domain = domain + [("company_id", "=", company.id)]

        # If we can't find records for the employee's company, search for
        # ones without a specific company attached.
        #
        ids = init_obj.search(domain)
        if len(ids) == 0:
            domain = [("date", "<=", today_str), ("company_id", "=", False)]
            ids = init_obj.search(domain)

        for init in ids:
            if init.date <= dToday and (res is None or init.date > res.date):
                res = init

        return res
