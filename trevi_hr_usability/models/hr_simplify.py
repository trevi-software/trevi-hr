# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrVersion(models.Model):
    """Simplified Employee Contract/Version Interface.

    Odoo 19 merged ``hr_contract`` into ``hr`` and renamed ``hr.contract`` to
    ``hr.version``.  The employee's personal data (nationality, official
    identification, ...) now lives on the version and ``hr.employee`` only
    exposes it through ``_inherits``/``version_id``, so the customisations that
    used to be declared on ``hr.employee``/``hr.contract`` are declared here.
    """

    _inherit = "hr.version"

    @api.model
    def _default_country(self):
        cid = self.env["res.country"].search([("code", "=", "ET")], limit=1)
        if cid:
            return cid[0]

    country_id = fields.Many2one(default=lambda self: self._default_country())

    @api.model
    def _default_employee(self):
        if self.env.context is not None:
            e_ids = self.env.context.get("search_default_employee_id", False)
            if e_ids:
                return e_ids[0]

    employee_id = fields.Many2one(default=lambda self: self._default_employee())

    employee_dept_id = fields.Many2one(
        string="Default Dept Id",
        related="employee_id.department_id",
        comodel_name="hr.department",
    )

    @api.onchange("employee_id")
    def onchange_employee_id(self):
        if self.employee_id:
            dept = self.employee_id.department_id
            self.employee_dept_id = dept.id
        else:
            self.employee_dept_id = False

    @api.constrains("identification_id")
    def _check_unique_identification_id(self):
        """Official identification numbers must be unique.

        Odoo 19 no longer stores ``identification_id`` on ``hr.employee`` (it is
        a related field delegating to ``hr.version``), so the historical
        ``unique(identification_id)`` SQL constraint cannot be kept as-is.  A
        single employee may have several versions carrying the same number, so
        the uniqueness is enforced per employee, i.e. one official
        identification number cannot be used by two different employees.
        """

        for version in self.filtered("identification_id"):
            duplicate = (
                self.env["hr.version"]
                .sudo()
                .search_count(
                    [
                        ("identification_id", "=", version.identification_id),
                        ("employee_id", "!=", version.employee_id.id),
                    ]
                )
            )
            if duplicate:
                raise ValidationError(
                    self.env._("Official Identifications must be unique!")
                )


class HrJob(models.Model):
    _inherit = "hr.job"

    no_of_employee = fields.Integer(
        string="Current Number of Employees",
        compute="_compute_employees",
        help="Number of employees currently occupying this job position.",
    )
    expected_employees = fields.Integer(
        compute="_compute_employees",
        string="Total Forecasted Employees",
        help="Expected number of employees for this job position after new "
        "recruitment.",
    )

    @api.depends("no_of_recruitment", "employee_ids.job_id", "employee_ids.active")
    def _compute_employees(self):
        contract_data = self.env["hr.version"]._read_group(
            [
                ("job_id", "in", self.ids),
                ("contract_date_end", "<=", fields.Date.today()),
            ],
            ["job_id"],
            ["__count"],
        )
        result = {job.id: count for job, count in contract_data}
        for record in self:
            record.no_of_employee = result.get(record.id, 0)
            record.expected_employees = record.no_of_employee + record.no_of_recruitment
