# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrSalaryRule(models.Model):

    _inherit = "hr.salary.rule"

    benefit_id = fields.Many2one(string="Benefit", comodel_name="hr.benefit")
    has_premium_payment = fields.Boolean(string="Premium payment?")
