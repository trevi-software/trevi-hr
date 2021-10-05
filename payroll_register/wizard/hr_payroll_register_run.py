# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, exceptions, fields, models


class PayrollRegisterRun(models.TransientModel):

    _name = "hr.payroll.register.run"
    _description = "Pay Slip Creation"

    department_ids = fields.Many2many(
        string="Departments",
        comodel_name="hr.department",
        relation="hr_department_payslip_run_rel",
        column1="register_id",
        column2="register_run_id",
    )

    def create_payslip_runs(self):

        self.ensure_one()
        Employee = self.env["hr.employee"]
        Payslip = self.env["hr.payslip"]
        PayslipRun = self.env["hr.payslip.run"]
        PayrollRegister = self.env["hr.payroll.register"]

        register_id = self.env.context.get("active_id", False)
        if not register_id:
            raise exceptions.ValidationError(
                _("Programming Error !")
                + "\n"
                + _("Unable to determine Payroll Register Id.")
            )
        pr = PayrollRegister.browse(register_id)

        if not self.department_ids:
            raise exceptions.UserError(
                _("Warning !")
                + "\n"
                + _("No departments selected for payslip generation.")
            )

        # Create a payslip batch for each department, and then for each employee
        # in a department create a pay slip and attach it to the payslip batch.
        #
        for dept in self.department_ids:
            run_res = {
                "name": dept.complete_name,
                "date_start": pr.date_start,
                "date_end": pr.date_end,
                "register_id": register_id,
            }
            run_id = PayslipRun.create(run_res)

            slip_ids = self.env["hr.payslip"]
            ee_ids = Employee.search([("department_id", "=", dept.id)], order="name")
            for ee in ee_ids:
                res = {
                    "employee_id": ee.id,
                    "payslip_run_id": run_id.id,
                    "date_from": pr.date_start.date(),
                    "date_to": pr.date_end.date(),
                }
                slip_ids |= Payslip.create(res)
            for s in slip_ids:
                s.onchange_employee()
            slip_ids.compute_sheet()

        pr.set_denominations()

        return {"type": "ir.actions.act_window_close"}
