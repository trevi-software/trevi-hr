# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2016 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PayrollPeriod(models.Model):
    _inherit = "hr.payroll.period"

    register_id = fields.Many2one("hr.payroll.register", "Payroll register")


class PayrollRegister(models.Model):
    _inherit = "hr.payroll.register"

    period_id = fields.Many2one("hr.payroll.period", "Payroll period")


class PayslipException(models.Model):

    _inherit = "hr.payslip.exception"

    def button_recalculate(self):

        for ex in self:
            period = ex.slip_id.payslip_run_id.register_id.period_id
            period.rerun_payslip(ex.slip_id)
