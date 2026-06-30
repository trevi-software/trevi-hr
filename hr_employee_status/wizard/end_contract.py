# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


import logging
_logger = logging.getLogger(__name__)


class EmployeeSetInactive(models.TransientModel):

    _name = "hr.contract.end"
    _description = "Employee De-Activation Wizard"

    @api.model
    def _get_contract(self):

        return self.env.context.get("end_contract_id", False)

    @api.model
    def _get_employee(self):

        contract_id = self.env.context.get("end_contract_id", False)
        if not contract_id:
            _logger.warning("No end_contract_id found in context")
            return False

        data = self.env["hr.contract"].browse(contract_id).read(["employee_id"])
        return data[0]["employee_id"] if data else False

    contract_id = fields.Many2one(
        comodel_name="hr.contract",
        default=lambda self: self._get_contract(),
        readonly=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        default=lambda self: self._get_employee(),
        required=True,
        readonly=True,
    )
    date = fields.Date(required=True, default=fields.Date.today())
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
        self.contract_id.setup_pending_done(vals)
        self.contract_id.signal_close()

        return {"type": "ir.actions.act_window_close"}
