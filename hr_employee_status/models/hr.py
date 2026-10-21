# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import logging
from datetime import date

from odoo import fields, models
from odoo.exceptions import UserError

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
                    ee.version_id.trial_date_end
                    and ee.version_id.trial_date_end > date.today()
                ):
                    raise UserError(
                        self.env._(
                            "The employee status may not be set to \
                        active before the trial period is over."
                        )
                    )
        return super().write(vals)

    def action_end_contract(self):
        """Open the de-activation wizard for the employee's current version."""
        self.ensure_one()

        return self.version_id.end_contract()

    def set_state_active(self, status="active"):
        for ee in self:
            if ee.status and ee.status in ("separation", "inactive"):
                version = ee.version_id
                # Re-open the contract: the old code called
                # ``contract.signal_reactivate()``, which dropped an end date
                # that had already passed.
                if (
                    version
                    and version.contract_date_end
                    and version.contract_date_end <= date.today()
                ):
                    version.contract_date_end = False
                ee.write(
                    {
                        "active": True,
                        "status": status,
                    }
                )

    def set_state_separation(self):
        self.write({"status": "separation"})

    def set_state_inactive(self):
        self.write(
            {
                "active": False,
                "status": "inactive",
            }
        )

    def signal_reactivate(self):
        self.set_state_active()

        return True
