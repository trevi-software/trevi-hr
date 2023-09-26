# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProcessingWizard(models.TransientModel):
    _inherit = "hr.payroll.processing"

    @api.model
    def _get_contracts(self):

        res = super()._get_contracts()
        if len(res) > 0:
            pp_id = self._get_pp()
            if pp_id:
                pp = self.env["hr.payroll.period"].browse(pp_id)
                if pp.schedule_id.use_operating_units:
                    res = res.filtered(
                        lambda c: c.operating_unit_id == pp.operating_unit_id
                    )
        return res

    contract_ids = fields.Many2many(default=_get_contracts)

    def get_period_schedule_contracts(self, period):
        """Get contracts attached to payroll schedule of 'period'."""

        res = super().get_period_schedule_contracts(period)
        if period.schedule_id.use_operating_units:
            res = res.filtered(
                lambda c: c.operating_unit_id == period.operating_unit_id
            )
        return res

    def create_payslip_runs(self, register_values, dept_ids):

        if self.payroll_period_id.operating_unit_id:
            register_values.update(
                {"operating_unit_id": self.payroll_period_id.operating_unit_id.id}
            )
        return super().create_payslip_runs(register_values, dept_ids)
