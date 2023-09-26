# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, models


class HrPayrollPeriod(models.Model):

    _inherit = "hr.payroll.period"

    @api.model
    def payslip_create_hook(self, dictCreate):

        if dictCreate.get("run_id", False):
            run = self.env["hr.payslip.run"].browse(dictCreate["run_id"])
            if run.journal_id:
                dictCreate.update({"journal_id": run.journal_id.id})
        return dictCreate
