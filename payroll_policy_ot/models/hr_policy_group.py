# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PolicyGroup(models.Model):

    _name = "hr.policy.group"
    _inherit = "hr.policy.group"

    ot_policy_ids = fields.Many2many(
        string="Overtime Policy",
        comodel_name="hr.policy.ot",
        relation="hr_policy_group_ot_rel",
        column1="group_id",
        column2="ot_id",
    )
