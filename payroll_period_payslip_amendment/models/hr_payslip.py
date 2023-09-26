# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def get_inputs(self, contracts, date_from, date_to):

        # Modify all the layers below to use the dates from the payroll period
        #
        periods = self.env["hr.payroll.period"].search(
            [
                ("date_start", "<=", date_to),
                ("date_end", ">=", date_from),
            ]
        )
        if periods:
            date_from = periods[0].date_start
            date_to = periods[0].date_end

        return super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
