# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    department_id = fields.Many2one(compute="_compute_contract", store=True)
    job_id = fields.Many2one(compute="_compute_contract", store=True)

    @api.depends("contract_id")
    def _compute_contract(self):
        for employee in self.filtered("contract_id"):
            employee.job_id = employee.contract_id.job_id
            employee.department_id = employee.contract_id.department_id

    @api.depends("contract_id", "contract_id.state", "contract_id.kanban_state")
    def _compute_contract_warning(self):
        for employee in self:
            employee.contract_warning = (
                not employee.contract_id
                or employee.contract_id.kanban_state == "blocked"
                or employee.contract_id.state not in ["open", "trial"]
            )

    def _get_contracts(self, date_from, date_to, states=["open"], kanban_state=False):

        # Over-ride base class method to includes Closed/Ended contracts. Useful
        # when multiple consecutive contracts occur in a payroll period.
        #
        default_states = ["open"]
        if states == default_states:
            states = ["open", "close"]

        return super(HrEmployee, self)._get_contracts(
            date_from, date_to, states=states, kanban_state=False
        )
