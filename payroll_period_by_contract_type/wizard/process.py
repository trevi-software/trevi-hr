# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from odoo.addons.payroll_period_processing.wizard.process import DEFAULT_BATCHBY


class ProcessPayroll(models.TransientModel):
    _inherit = "hr.payroll.processing"

    @api.model
    def _get_batch_type(self):
        pp_id = self._get_pp()
        if pp_id:
            pp = self.env["hr.payroll.period"].browse(pp_id)
            if pp.schedule_id.batch_by_contract_type:
                return True
        return False

    batch_by_contract_type = fields.Boolean(
        default=_get_batch_type,
        help="If checked create payslip batches by contract type.",
    )

    def get_batch_criteria(self):
        if self.batch_by_contract_type:
            return "contract_type"
        return super().get_batch_criteria()

    def _create_batches(
        self,
        register,
        contracts,
        departments,
        date_start,
        date_end,
        batch_by=DEFAULT_BATCHBY,
    ):

        batches = super()._create_batches(
            register, contracts, departments, date_start, date_end, batch_by=batch_by
        )
        if batch_by != "contract_type":
            return batches

        # batch_by == "contract_type"
        employees = self.env["hr.employee"]
        ctypes = self.env["hr.contract.type"].search([])
        for dept in departments:
            employees |= self._get_employees_from_department(
                dept, contracts, date_start, date_end
            )

        for ctype in ctypes:
            ees = employees.filtered(
                lambda e: contracts.filtered(lambda c: c.employee_id == e)[
                    0
                ].contract_type_id
                == ctype
            )
            if len(ees) == 0:
                continue

            run_res = {
                "name": f"{ctype.name} Staff",
                "date_start": date_start,
                "date_end": date_end,
                "register_id": register.id,
                "period_id": register.period_id.id,
                "department_ids": [(6, 0, [dept.id])],
            }
            batch = self.env["hr.payslip.run"].create(run_res)

            # Create a pay slip for each employee in each department that has
            # a contract in the pay period schedule of this pay period
            payslips = self.env["hr.payslip"]
            for ee in ees:
                if not self.payroll_period_id.process_employee(ee.id):
                    continue

                payslips |= self.payroll_period_id.create_payslip(ee.id, batch.id)

            # Calculate payroll for all the pay slips in this batch (run)
            payslips.compute_sheet()
            batches |= batch

        return batches
