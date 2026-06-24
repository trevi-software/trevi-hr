# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models


class HrContract(models.Model):
    _inherit = "hr.contract"

    def condition_trial_period(self):
        res = super().condition_trial_period()
        if (
            self.trial_date_end
            and self.employee_id.hire_date
            and self.employee_id.hire_date < self.date_start
        ):
            res = False
        return res
