# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrContract(models.Model):

    _inherit = "hr.contract"

    @api.model
    def _get_pay_sched(self):

        iv = self.get_latest_initial_values()
        if iv is not None and iv.pay_sched_id:
            return iv.pay_sched_id.id
        return False

    pps_id = fields.Many2one(default=_get_pay_sched)
