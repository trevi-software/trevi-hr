##############################################################################
#
#    Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
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

from odoo import models, fields, api, _


class HrEmployee(models.Model):
    """Simplified Employee Record Interface."""

    _name = 'hr.employee'
    _inherit = 'hr.employee'
    _sql_constraints = [
        (
            'unique_identification_id',
            'unique(identification_id)',
            _('Official Identifications must be unique!')
        ),
    ]

    @api.model
    def _default_country(self):

        cid = self.env['res.country'].search([('code', '=', 'ET')])
        if cid:
            return cid[0]

    country_id = fields.Many2one(default=_default_country)
    job_id = fields.Many2one(
        related='contract_id.job_id',
        comodel_name="hr.job",
        string="Job",
        readonly=True
    )


class HrContract(models.Model):

    _inherit = 'hr.contract'

    @api.model
    def _default_employee(self):

        if self.env.context is not None:
            e_ids = self.env.context.get('search_default_employee_id', False)
            if e_ids:
                return e_ids[0]

    employee_id = fields.Many2one(default=_default_employee)
    employee_dept_id = fields.Many2one(
        string="Default Dept Id",
        related='employee_id.department_id',
        comodel_name='hr.department'
    )

    @api.onchange('employee_id')
    def onchange_employee_id(self):

        dom = {'job_id': [], }
        if self.employee_id:
            dept = self.employee_id.department_id
            self.employee_dept_id = dept.id
            dom['job_id'] = [('department_id', '=', dept.id)]
        return {'domain': dom}


class HrJob(models.Model):

    _name = 'hr.job'
    _inherit = 'hr.job'

    no_of_employee = fields.Integer(
        string="Current Number of Employees",
        compute='_compute_employees',
        help='Number of employees currently occupying this job position.',
    )
    expected_employees = fields.Integer(
        compute='_compute_employees',
        string='Total Forecasted Employees',
        help='Expected number of employees for this job position after new recruitment.',
    )

    @api.depends('no_of_recruitment', 'employee_ids.job_id', 'employee_ids.active')
    def _compute_employees(self):
        contract_data = self.env['hr.contract'].read_group(
            [
                ('job_id', 'in', self.ids),
                ('date_end', '<=', fields.Date.today())
            ], ['job_id'], ['job_id']
        )
        result = dict((data['job_id'][0], data['job_id_count']) for data in contract_data)
        for record in self:
            record.no_of_employee = result.get(record.id, 0)
            record.expected_employees = result.get(record.id, 0) + record.no_of_recruitment
