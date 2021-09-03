##############################################################################
#
#    Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class HrJob(models.Model):

    _inherit = 'hr.job'

    category_ids = fields.Many2many(
        string='Associated Tags',
        comodel_name='hr.employee.category',
        relation='job_category_rel',
        column1='job_id',
        column2='category_id'
    )


class HrContract(models.Model):

    _name = 'hr.contract'
    _inherit = 'hr.contract'

    @api.model
    def _remove_tags(self, employee_id, job_id):

        if not employee_id or not job_id:
            return

        ee_obj = self.env['hr.employee']
        eedata = ee_obj.browse(employee_id).read(['category_ids'])
        job = self.env['hr.job'].browse(job_id)
        for tag in job.category_ids:
            if tag.id in eedata['category_ids']:
                ee_obj.browse(employee_id).write({'category_ids': [(3, tag.id)]})
        return

    @api.model
    def _tag_employees(self, employee_id, job_id):

        if not employee_id or not job_id:
            return

        ee_obj = self.env['hr.employee']
        eedata = ee_obj.browse(employee_id).read(['category_ids'])
        job = self.env['hr.job'].browse(job_id)
        for tag in job.category_ids:
            if tag.id not in eedata['category_ids']:
                ee_obj.browse(employee_id).write({'category_ids': [(4, tag.id)]})
        return

    @api.model
    def create(self, vals):

        res = super(HrContract, self).create(vals)

        self._tag_employees(vals.get('employee_id', False), vals.get('job_id', False))
        return res

    def write(self, vals):

        prev_data = self.read(['job_id'])
        res = super(HrContract, self).write(vals)

        # Go through each record and delete tags associated with the previous job, then
        # add the tags of the new job.
        #
        for contract in self:
            for data in prev_data:
                if data['id'] == contract.id:
                    if not vals.get('job_id', False) or (data.get('job_id', False) and data['job_id'][0] != vals['job_id']):
                        prev_job_id = data.get('job_id', False) and data['job_id'][0] or False
                        self._remove_tags(contract.employee_id.id, prev_job_id)
                        if vals.get('job_id', False):
                            self._tag_employees(contract.employee_id.id, contract.job_id.id)

        return res
