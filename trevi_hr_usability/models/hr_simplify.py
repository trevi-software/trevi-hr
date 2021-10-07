# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class HrEmployee(models.Model):
    """Simplified Employee Record Interface."""

    _name = "hr.employee"
    _inherit = "hr.employee"
    _sql_constraints = [
        (
            "unique_identification_id",
            "unique(identification_id)",
            _("Official Identifications must be unique!"),
        ),
    ]

    @api.model
    def _default_country(self):

        cid = self.env["res.country"].search([("code", "=", "ET")])
        if cid:
            return cid[0]

    country_id = fields.Many2one(default=_default_country)
    job_id = fields.Many2one(
        related="contract_id.job_id", comodel_name="hr.job", string="Job", readonly=True
    )


class HrContract(models.Model):

    _inherit = "hr.contract"

    @api.model
    def _default_employee(self):

        if self.env.context is not None:
            e_ids = self.env.context.get("search_default_employee_id", False)
            if e_ids:
                return e_ids[0]

    employee_id = fields.Many2one(default=_default_employee)
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


class HrJob(models.Model):

    _name = "hr.job"
    _inherit = "hr.job"

    no_of_employee = fields.Integer(
        string="Current Number of Employees",
        compute="_compute_employees",
        help="Number of employees currently occupying this job position.",
    )
    expected_employees = fields.Integer(
        compute="_compute_employees",
        string="Total Forecasted Employees",
        help="Expected number of employees for this job position after new recruitment.",
    )

    @api.depends("no_of_recruitment", "employee_ids.job_id", "employee_ids.active")
    def _compute_employees(self):
        contract_data = self.env["hr.contract"].read_group(
            [("job_id", "in", self.ids), ("date_end", "<=", fields.Date.today())],
            ["job_id"],
            ["job_id"],
        )
        result = {data["job_id"][0]: data["job_id_count"] for data in contract_data}
        for record in self:
            record.no_of_employee = result.get(record.id, 0)
            record.expected_employees = (
                result.get(record.id, 0) + record.no_of_recruitment
            )
