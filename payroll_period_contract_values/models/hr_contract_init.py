# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ContractInit(models.Model):
    _inherit = "hr.contract.init"

    pay_sched_id = fields.Many2one(
        string="Payroll Period Schedule",
        comodel_name="hr.payroll.period.schedule",
        required=False,
    )
