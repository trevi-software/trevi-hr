# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class EmployeeSetInactive(models.TransientModel):
    _name = "hr.version.end"
    _description = "Employee De-Activation Wizard"

    @api.model
    def _get_version(self):
        return self.env.context.get("end_version_id", False)

    @api.model
    def _get_employee(self):
        version_id = self.env.context.get("end_version_id", False)
        if not version_id:
            _logger.warning("No end_version_id found in context")
            return False

        data = self.env["hr.version"].browse(version_id).read(["employee_id"])
        return data[0]["employee_id"] if data else False

    version_id = fields.Many2one(
        comodel_name="hr.version",
        default=lambda self: self._get_version(),
        readonly=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        default=lambda self: self._get_employee(),
        required=True,
        readonly=True,
    )
    date = fields.Date(required=True, default=fields.Date.today)
    reason_id = fields.Many2one(
        comodel_name="hr.employee.termination.reason", required=True
    )
    notes = fields.Text()

    def set_employee_inactive(self):
        self.ensure_one()
        vals = {
            "name": self.date,
            "employee_id": self.employee_id.id,
            "reason_id": self.reason_id.id,
            "notes": self.notes,
        }
        # The separation ends the contract on its effective date (see
        # ``hr.employee.termination.create``).
        self.version_id.start_separation(vals)

        return {"type": "ir.actions.act_window_close"}
