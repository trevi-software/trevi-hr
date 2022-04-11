# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import api, fields, models


class Benefits(models.TransientModel):

    _name = "hr.employee.wizard.benefit"
    _description = "New Hire Benefits"

    @api.model
    def _find_contract_start_date(self):
        if not self.env.context.get("csdate"):
            return datetime.now().date()
        return fields.Date.from_string(self.env.context.get("csdate"))

    wizard_id = fields.Many2one("hr.employee.wizard.new", "Wizard")
    benefit_id = fields.Many2one("hr.benefit", "Benefit", required=True)
    effective_date = fields.Date(required=True, default=_find_contract_start_date)
    end_date = fields.Date()
    adv_override = fields.Boolean("Override Advantage")
    prm_override = fields.Boolean("Override Premium")
    adv_amount = fields.Float("Advantage Amount", digits="Payroll Rate")
    prm_amount = fields.Float("Premium Amount", digits="Payroll Rate")
    prm_total = fields.Float("Premium Total", digits="Payroll Rate")
