# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrPayslipWorkedDays(models.Model):
    _name = "hr.payslip.benefit"
    _description = "Payslip Benefits"
    _order = "payslip_id, sequence"

    name = fields.Char(string="Description", required=True)
    payslip_id = fields.Many2one(
        "hr.payslip", "Pay Slip", required=True, ondelete="cascade", index=True
    )
    code = fields.Char(required=True, help="The code used in the salary rules")
    sequence = fields.Integer(required=True, index=True, default=10)
    qty = fields.Integer(
        "Quantity",
        help="The number of policies of this benefit that apply to this payslip.",
    )
    ppf = fields.Float(
        "Payroll Period Factor",
        help="The percentage of this benefit applied to the payslip. Directly "
        "related to the percentage of the contract that applies to the payslip.",
    )
    earnings = fields.Float()
    deductions = fields.Float()
