# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import logging
from datetime import date

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    # 'state' was being used by hr_attendance (although not anymore)
    status = fields.Selection(
        selection=[
            ("new", "New-Hire"),
            ("trial", "Trial Period"),
            ("active", "Active"),
            ("separation", "Pending Separation"),
            ("inactive", "Inactive"),
            ("reactivated", "Re-Activated"),
        ],
        default="new",
        readonly=True,
    )
    inactive_ids = fields.One2many(
        comodel_name="hr.employee.termination",
        inverse_name="employee_id",
        string="Separation Records",
    )

    def write(self, vals):
        for ee in self:
            if (
                "status" in vals
                and vals.get("status") == "active"
                and ee.status == "trial"
            ):
                if (
                    ee.contract_id.trial_date_end
                    and ee.contract_id.trial_date_end > date.today()
                ):
                    raise UserError(
                        _(
                            "The employee status may not be se to \
                        active before the trial period is over."
                        )
                    )
        return super(HrEmployee, self).write(vals)

    def set_state_active(self, status="active"):

        for ee in self:
            if ee.status and ee.status == "separation":
                ee.write(
                    {
                        "active": True,
                        "status": status,
                    }
                )

    def set_state_separation(self):

        for ee in self:
            ee.write(
                {
                    "status": "separation",
                }
            )

    def set_state_inactive(self):

        for ee in self:
            ee.write(
                {
                    "active": False,
                    "status": "inactive",
                }
            )

    def signal_reactivate(self):

        for employee in self:
            employee.set_state_active()

        return True
