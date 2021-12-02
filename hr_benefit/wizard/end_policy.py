# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PolicyEnd(models.TransientModel):

    _name = "hr.benefit.policy.end"
    _description = "Benefit Policy Termination Wizard"

    date = fields.Date(string="End Date", required=True, default=fields.Date.today())

    @api.model
    def _get_policy(self):

        return self.env.context.get("end_benefit_policy_id", False)

    def end_policy(self):

        policy_id = self._get_policy()
        if not policy_id:
            raise ValidationError(_("Unable to determine Benefit Policy."))

        policy = self.env["hr.benefit.policy"].browse(policy_id)
        policy.end_date = self.date
        policy.state_done()
        return {"type": "ir.actions.act_window_close"}
