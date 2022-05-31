# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class HrPayslip(models.Model):

    _inherit = "hr.payslip"

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contracts: Browse record of contracts
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """

        res = super().get_worked_day_lines(contracts, date_from, date_to)

        leave_types = self.env["hr.leave.type"].search([])
        leave_names = leave_types.mapped("name")

        # Change worked_days record codes from leave names to leave codes
        for r in res:
            if r["code"] == "WORK100":
                continue
            elif r["code"] in leave_names:
                lv_list = leave_types.filtered(lambda lvt: lvt.name == r["code"])
                if len(lv_list) > 0:
                    r["code"] = lv_list[0].code

        return res
