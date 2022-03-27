# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

_l = logging.getLogger(__name__)


class HrJob(models.Model):

    _inherit = "hr.job"
    _parent_store = True
    _order = "parent_path"

    department_manager = fields.Boolean()
    parent_id = fields.Many2one(
        string="Immediate Superior", comodel_name="hr.job", ondelete="cascade"
    )
    child_ids = fields.One2many(
        string="Immediate Subordinates",
        comodel_name="hr.job",
        inverse_name="parent_id",
    )
    all_child_ids = fields.Many2many(
        compute="_compute_all_child_ids", comodel_name="hr.job"
    )
    parent_path = fields.Char(index=True)

    def _compute_all_child_ids(self):
        for rec in self:
            rec.child_ids = self.search([("parent_id", "child_of", rec.id)])

    @api.constrains("parent_id")
    def _check_job_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_("Error! You cannot create recursive jobs."))

    def write(self, vals):

        res = super(HrJob, self).write(vals)

        dept_obj = self.env["hr.department"]
        if vals.get("department_manager", False):
            for job in self:
                dept_id = False
                if vals.get("department_id", False):
                    dept_id = vals["department_id"]
                else:
                    dept_id = job.department_id.id
                employee_id = False
                for ee in job.employee_ids:
                    employee_id = ee.id
                if employee_id:
                    dept_obj.browse(dept_id).write({"manager_id": employee_id})
        elif vals.get("department_id", False):
            for job in self:
                if job.department_manager:
                    employee_id = False
                    for ee in job.employee_ids:
                        employee_id = ee.id
                    dept_obj.browse(vals["department_id"]).write(
                        {"manager_id": employee_id}
                    )
        elif vals.get("parent_id", False):
            parent_job = self.browse(vals["parent_id"])
            parent_id = False
            for ee in parent_job.employee_ids:
                parent_id = ee.id
            for job in self:
                for ee in job.employee_ids:
                    ee.parent_id = parent_id

        return res


class HrContract(models.Model):

    _name = "hr.contract"
    _inherit = "hr.contract"

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HrContract, self).create(vals_list)

        if not any([vals.get("job_id", False) for vals in vals_list]):
            return res

        Employee = self.env["hr.employee"]
        Job = self.env["hr.job"]

        for vals in vals_list:

            job = Job.browse(vals["job_id"])

            if job and job.parent_id:
                parent_ee_id = False
                for employee in job.parent_id.employee_ids:
                    parent_ee_id = employee.id
                if parent_ee_id and vals.get("employee_id"):
                    Employee.browse(vals["employee_id"]).write(
                        {"parent_id": parent_ee_id}
                    )

            # Write any employees with jobs that are immediate descendants of this job
            if job:
                job_child_ids = []
                [job_child_ids.append(child.id) for child in job.child_ids]
                if len(job_child_ids) > 0:
                    ee_ids = Employee.search([("job_id", "in", job_child_ids)])
                    if len(ee_ids) > 0:
                        parent_ee_id = False
                        for employee in job.employee_ids:
                            parent_ee_id = employee.id
                        if parent_ee_id:
                            ee_ids.write({"parent_id": parent_ee_id})
        return res

    def write(self, vals):

        res = super(HrContract, self).write(vals)

        if not vals.get("job_id", False):
            return res

        ee_obj = self.env["hr.employee"]

        job = self.env["hr.job"].browse(vals["job_id"])

        # Write the employee's manager
        if job and job.parent_id:
            parent_id = False
            for ee in job.parent_id.employee_ids:
                parent_id = ee.id
            if parent_id:
                for contract in self:
                    contract.employee_id.parent_id = parent_id

        # Write any employees with jobs that are immediate descendants of this job
        if job:
            job_child_ids = []
            [job_child_ids.append(child.id) for child in job.child_ids]
            if len(job_child_ids) > 0:
                ee_ids = ee_obj.search(
                    [("job_id", "in", job_child_ids), ("active", "=", True)]
                )
                if len(ee_ids) > 0:
                    parent_id = False
                    for ee in job.employee_ids:
                        parent_id = ee.id
                    if parent_id:
                        ee_ids.write({"parent_id": parent_id})

        return res


class HrDepartment(models.Model):

    _inherit = "hr.department"

    def write(self, vals):

        # Get previous manager(s)
        manager_ids = []
        if "manager_id" in vals:
            for rec in self:
                if rec.manager_id and rec.manager_id.id not in manager_ids:
                    manager_ids.append(rec.manager_id.id)

        res = super(HrDepartment, self).write(vals)

        Employee = self.env["hr.employee"]

        if "manager_id" in vals:
            manager_ids.append(vals["manager_id"])
            ee_ids = Employee.search(
                [
                    ("department_id", "in", self.ids),
                    ("active", "=", True),
                    ("id", "not in", manager_ids),
                ]
            )
            ee_ids.write({"parent_id": vals["manager_id"]})

        return res
