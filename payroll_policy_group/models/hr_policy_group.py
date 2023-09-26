# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PolicyGroup(models.Model):

    _name = "hr.policy.group"
    _description = "HR Policy Group"

    name = fields.Char(required=True)
    contract_ids = fields.One2many(
        string="Contracts", comodel_name="hr.contract", inverse_name="policy_group_id"
    )


class ContractInit(models.Model):

    _inherit = "hr.contract.init"

    policy_group_id = fields.Many2one(
        string="Policy Group",
        comodel_name="hr.policy.group",
    )


class HrContract(models.Model):

    _inherit = "hr.contract"

    @api.model
    def _get_policy_group(self):

        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.policy_group_id:
            res = init.policy_group_id.id
        return res

    policy_group_id = fields.Many2one(
        string="Policy Group",
        comodel_name="hr.policy.group",
        default=_get_policy_group,
    )
