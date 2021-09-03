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

from datetime import date

from odoo import models, fields, api, _


class HrHolidays(models.Model):

    _name = 'hr.holidays.public'
    _description = 'Public Holidays'
    _rec_name = 'year'
    _order = "year"
    _sql_constraints = [
        (
            'year_unique',
            'UNIQUE(year)',
            _('Duplicate year!')
        ),
    ]

    year = fields.Char(string="calendar Year", required=True)
    line_ids = fields.One2many(
        string='Holiday Dates',
        comodel_name='hr.holidays.public.line',
        inverse_name='holidays_id'
    )

    @api.model
    def is_public_holiday(self, dt):

        ph_ids = self.search([('year', '=', dt.year)])

        if len(ph_ids) == 0:
            return False

        for line in ph_ids[0].line_ids:
            if dt == line.date:
                return True

        return False

    @api.model
    def get_holidays_list(self, year):

        res = []
        ph_ids = self.search([('year', '=', year)])

        if len(ph_ids) == 0:
            return res
        [res.append(l.date) for l in ph_ids[0].line_ids]
        return res


class HrHolidaysLine(models.Model):

    _name = 'hr.holidays.public.line'
    _description = 'Public Holidays Lines'
    _order = "date, name desc"

    name = fields.Char(required=True)
    date = fields.Date(required=True)
    holidays_id = fields.Many2one(string='Holiday Calendar Year', comodel_name='hr.holidays.public')
    variable = fields.Boolean(string='Date may change')

