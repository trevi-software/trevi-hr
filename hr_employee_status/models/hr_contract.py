# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrContract(models.Model):

    _inherit = "hr.contract"

    def re_activate(self):

        for contract in self:

            term_obj = self.env["hr.employee.termination"]
            term_ids = term_obj.search(
                [
                    ("employee_id", "=", contract.employee_id.id),
                    ("state", "in", ["draft", "confirm"]),
                ]
            )

            if len(term_ids) == 0:

                # Trigger a status change of the employee and his contract(s)
                contract.employee_id.signal_workflow("signal_active")
                if contract.state == "pending_done":
                    contract.signal_workflow("signal_open")
            else:

                for term in term_ids:

                    # Trigger a status change of the employee and his contract(s)
                    if term.state == "confirm":
                        term.signal_workflow("signal_cancel")
                    else:
                        term.unlink()

        return True

    def end_contract(self):

        if len(self.ids) == 0:
            return False

        ctx = dict(self.env.context)
        ctx.update({"end_contract_id": self.ids[0]})
        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.contract.end",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": ctx,
        }

    @api.model
    def update_state(self):

        # New contract with trial period
        employees = self.search(
            [
                ("state", "=", "draft"),
                ("kanban_state", "=", "done"),
                ("date_start", "<=", fields.Date.to_string(date.today())),
                ("trial_date_end", ">=", fields.Date.to_string(date.today())),
            ]
        ).mapped("employee_id")
        employees.write({"status": "trial"})

        # New contract without trial period
        employees = self.search(
            [
                ("state", "=", "draft"),
                ("kanban_state", "=", "done"),
                ("date_start", "<=", fields.Date.to_string(date.today())),
                "|",
                ("trial_date_end", "=", False),
                ("trial_date_end", "<", fields.Date.to_string(date.today())),
            ]
        ).mapped("employee_id")
        employees.write({"status": "active"})

        # Trial period has ended
        employees = self.search(
            [
                ("state", "=", "trial"),
                (
                    "trial_date_end",
                    "<=",
                    fields.Date.to_string(date.today() - relativedelta(days=1)),
                ),
            ]
        ).mapped("employee_id")
        employees.write({"status": "active"})

        # Contracts have ended
        contracts = self.search(
            [
                ("state", "=", "open"),
                "|",
                (
                    "date_end",
                    "<=",
                    fields.Date.to_string(date.today() + relativedelta(days=1)),
                ),
                (
                    "visa_expire",
                    "<=",
                    fields.Date.to_string(date.today() + relativedelta(days=1)),
                ),
            ]
        )
        for c in contracts:
            vals = {
                "name": c.date_end and c.date_end,
                "employee_id": c.employee_id.id,
                "reason_id": self.env.ref("hr_employee_status.term_contract_end").id,
            }
            c.setup_pending_done(vals)

        return super(HrContract, self).update_state()

    def signal_confirm(self):
        res = super(HrContract, self).signal_confirm()
        for c in self:
            if c.condition_trial_period():
                c.employee_id.status = "trial"
            else:
                c.employee_id.status = "active"
        return res

    def setup_pending_done(self, term_vals):
        """Start employee deactivation process."""

        term_obj = self.env["hr.employee.termination"]
        dToday = datetime.now().date()

        for contract in self:
            # If employee is already inactive simply end the contract
            if not contract.employee_id.active:
                return

            # Ensure there are not other open contracts
            #
            open_contract = False
            for c2 in contract.employee_id.contract_ids:
                if c2.id == contract.id or c2.state == "draft":
                    continue

                if (not c2.date_end or c2.date_end > dToday) and c2.state != "done":
                    open_contract = True

            # Don't create an employment termination if the employee has an open contract or
            # if this contract is already in the 'done' state. If there is an open contract
            # simply terminate this one without any further action.
            if open_contract or contract.state == "close":
                return

            # Also skip creating an employment termination if there is already one in
            # progress for this employee.
            #
            term_ids = term_obj.search(
                [
                    ("employee_id", "=", contract.employee_id.id),
                    ("state", "in", ["draft", "confirm"]),
                ]
            )
            if len(term_ids) > 0:
                return

            term_obj.create(term_vals)
