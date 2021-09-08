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


class HrContract(models.Model):

    _name = "hr.contract"
    _inherit = "hr.contract"

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

    @api.model
    def create(self, vals):

        res = super(HrContract, self).create(vals)

        self._tag_employees(vals.get("employee_id", False), vals.get("job_id", False))
        return res

    def write(self, vals):

        prev_data = self.read(["job_id"])
        res = super(HrContract, self).write(vals)

        # Go through each record and delete tags associated with the previous job, then
        # add the tags of the new job.
        #
        for contract in self:
            for data in prev_data:
                if data["id"] == contract.id:
                    if not vals.get("job_id", False) or (
                        data.get("job_id", False)
                        and data["job_id"][0] != vals["job_id"]
                    ):
                        prev_job_id = (
                            data.get("job_id", False) and data["job_id"][0] or False
                        )
                        self._remove_tags(contract.employee_id.id, prev_job_id)
                        if vals.get("job_id", False):
                            self._tag_employees(
                                contract.employee_id.id, contract.job_id.id
                            )

        return res
