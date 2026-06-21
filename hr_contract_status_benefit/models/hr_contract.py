# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo import api, fields, models


class HrContract(models.Model):

    _inherit = "hr.contract"

    @api.model
    def update_state(self):

        # New contract
        contracts = self.search(
            [
                ("state", "=", "draft"),
                ("kanban_state", "=", "done"),
                ("date_start", "<=", fields.Date.to_string(date.today())),
            ]
        )
        for c in contracts:
            self.env["hr.benefit.policy"].search(
                [
                    ("employee_id", "=", c.employee_id.id),
                    ("start_date", "=", c.date_start),
                    ("state", "=", "draft"),
                ]
            ).state_open()

        return super().update_state()

    def signal_confirm(self):

        for contract in self:
            contract.employee_id.benefit_policy_ids.filtered(
                lambda p: p.start_date == contract.date_start and p.state == "draft"
            ).state_open()

        return super().signal_confirm()
