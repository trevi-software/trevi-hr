# Copyright (C) 2022 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PolicyGroup(models.Model):

    _inherit = "hr.policy.group"

    rounding_policy_ids = fields.Many2many(
        string="Rounding Policy",
        comodel_name="hr.policy.rounding",
    )
