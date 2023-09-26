# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PolicyGroup(models.Model):

    _inherit = "hr.policy.group"

    accr_policy_ids = fields.Many2many(
        string="Accrual Policy",
        comodel_name="hr.policy.accrual",
        relation="hr_policy_group_accr_rel",
        column1="group_id",
        column2="accr_id",
    )
