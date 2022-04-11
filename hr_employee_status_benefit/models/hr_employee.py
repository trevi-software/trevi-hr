# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    def set_state_inactive(self):

        for ee in self:

            inactive_date = False
            for term in ee.inactive_ids:
                if (
                    not inactive_date
                    or term.name > inactive_date
                    and term.state != "cancel"
                ):
                    inactive_date = term.name
            if inactive_date is False:
                inactive_date = fields.Date.today()

            for policy in ee.benefit_policy_ids:
                if policy.state not in ["done"]:
                    policy.end_date = inactive_date
                    policy.state_done()

        return super().set_state_inactive()
