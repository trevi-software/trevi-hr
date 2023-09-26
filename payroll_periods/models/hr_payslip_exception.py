# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrPayslipException(models.Model):

    _name = "hr.payslip.exception"
    _description = "Payroll Exception"

    name = fields.Char(required=True, readonly=True)
    rule_id = fields.Many2one(
        comodel_name="hr.payslip.exception.rule",
        string="Rule",
        ondelete="cascade",
        readonly=True,
    )
    slip_id = fields.Many2one(
        comodel_name="hr.payslip", string="Pay Slip", ondelete="cascade", readonly=True
    )
    severity = fields.Selection(related="rule_id.severity", store=True, readonly=True)
    ignore = fields.Boolean(string="Ignore", default=False)

    def button_ignore(self):

        self.write({"ignore": True})

    def button_unignore(self):

        self.write({"ignore": False})
