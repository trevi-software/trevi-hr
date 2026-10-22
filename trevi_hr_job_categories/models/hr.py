# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrJob(models.Model):
    _inherit = "hr.job"

    category_ids = fields.Many2many(
        string="Associated Tags",
        comodel_name="hr.employee.category",
        relation="job_category_rel",
        column1="job_id",
        column2="category_id",
    )


class HrVersion(models.Model):
    _inherit = "hr.version"

    @api.model
    def _remove_tags(self, employee_id, job_id):
        if not employee_id or not job_id:
            return

        employee = self.env["hr.employee"].browse(employee_id)
        job = self.env["hr.job"].browse(job_id)

        for tag in job.category_ids:
            if tag in employee.category_ids:
                employee.write({"category_ids": [(3, tag.id)]})

        return

    @api.model
    def _tag_employees(self, employee_id, job_id):
        if not employee_id or not job_id:
            return

        employee = self.env["hr.employee"].browse(employee_id)
        job = self.env["hr.job"].browse(job_id)

        for tag in job.category_ids:
            if tag not in employee.category_ids:
                employee.write({"category_ids": [(4, tag.id)]})

        return

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for vals in vals_list:
            self._tag_employees(
                vals.get("employee_id", False), vals.get("job_id", False)
            )
        return records

    def write(self, vals):
        # Only re-synchronize the employee tags when the job actually changes;
        # any other write must leave the tags untouched.
        if "job_id" not in vals:
            return super().write(vals)

        prev_jobs = {data["id"]: data.get("job_id") for data in self.read(["job_id"])}
        res = super().write(vals)

        # Go through each record and delete tags associated with the previous job, then
        # add the tags of the new job.
        #
        for version in self:
            prev_job = prev_jobs.get(version.id)
            prev_job_id = prev_job and prev_job[0] or False
            new_job_id = version.job_id.id or False

            if prev_job_id == new_job_id:
                continue

            if prev_job_id:
                self._remove_tags(version.employee_id.id, prev_job_id)
            if new_job_id:
                self._tag_employees(version.employee_id.id, new_job_id)

        return res
