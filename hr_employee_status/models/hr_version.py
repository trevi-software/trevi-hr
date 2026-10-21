# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class HrVersion(models.Model):
    """Employment status of an employee, driven by their contracts.

    In Odoo 19 the ``hr_contract`` module was merged into ``hr`` and
    ``hr.contract`` became ``hr.version``. The trevi contract state machine
    (``draft``/``trial``/``open``/``pending_done``/``close``/``cancel`` plus
    ``kanban_state``) is therefore gone and is not re-created here: instead of
    writing a state, the code uses the native flags - ``active`` for a live vs
    archived version, and the computed ``is_current``/``is_past``/``is_future``/
    ``is_in_contract`` - which derive from ``contract_date_start`` and
    ``contract_date_end`` (``date_start``/``date_end`` still exist as computed,
    searchable fields).
    """

    _inherit = "hr.version"

    def signal_close(self, date_end=None):
        """End this version on ``date_end`` (today when not given).

        Native replacement of the old ``state = 'close'`` write: a contract is
        ended by giving it an end date.
        """
        date_end = date_end or fields.Date.context_today(self)
        for version in self:
            if not version.contract_date_end or version.contract_date_end > date_end:
                version.contract_date_end = date_end

        return True

    def end_contract(self):
        """Action that opens the de-activation wizard for this version."""
        if not self.ids:
            return False

        ctx = dict(self.env.context)
        ctx.update({"end_version_id": self.ids[0]})
        return {
            "view_mode": "form",
            "res_model": "hr.version.end",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": ctx,
        }

    def re_activate(self):
        """Re-activate the employee and drop any pending separation."""
        term_obj = self.env["hr.employee.termination"]

        for version in self:
            term_ids = term_obj.search(
                [
                    ("employee_id", "=", version.employee_id.id),
                    ("state", "in", ["draft", "confirm"]),
                ]
            )

            if len(term_ids) == 0:
                # Trigger a status change of the employee and its contract
                version.employee_id.write(
                    {
                        "active": True,
                        "status": "active",
                    }
                )
                version.write(
                    {
                        "active": True,
                        "contract_date_end": False,
                    }
                )
            else:
                # Cancelling or deleting the separation gives the employee
                # status and the contract end date they had before.
                for term in term_ids:
                    if term.state == "confirm":
                        term.write({"state": "cancel"})
                    else:
                        term.unlink()

        return True

    def start_separation(self, term_vals):
        """Start the employee de-activation process.

        Called when a contract has ended and from the "End Contract" wizard. A
        separation is created only when the employee has no other running
        contract and no separation is already in progress. The old code also
        bailed out when the contract already was in the ``close`` state; that
        state does not exist any more, it is the caller that decides on the
        dates.
        """
        term_obj = self.env["hr.employee.termination"]
        today = fields.Date.context_today(self)

        for version in self:
            # If the employee is already inactive simply end the contract
            if not version.employee_id.active:
                continue

            # Ensure there are no other running contracts
            other_running = version.employee_id.version_ids.filtered(
                lambda v, current=version: v != current
                and v.contract_date_start
                and v.contract_date_start <= today
                and (not v.contract_date_end or v.contract_date_end > today)
            )
            if other_running:
                continue

            # Also skip creating an employment termination if there is already
            # one in progress for this employee.
            term_ids = term_obj.search(
                [
                    ("employee_id", "=", version.employee_id.id),
                    ("state", "in", ["draft", "confirm"]),
                ]
            )
            if len(term_ids) > 0:
                continue

            term_obj.create(term_vals)

        return True

    @api.model
    def update_employee_status(self):
        """Drive the employee status from the contract dates.

        Replaces the old ``hr.contract.update_state()`` override, which the
        ``hr_contract`` "Update Contract State" cron used to call. That cron,
        along with the ``state``/``kanban_state`` fields it maintained, is gone
        in 19.0, so the same intent is derived from the dates:

        * contract started and its trial period is still running -> ``trial``
        * contract started and the trial period is over -> ``active``
        * contract ended -> start the employee de-activation process
        """
        today = fields.Date.context_today(self)

        running = self.search(
            [
                ("contract_date_start", "<=", today),
                "|",
                ("contract_date_end", "=", False),
                ("contract_date_end", ">=", today),
            ]
        )

        on_trial = running.filtered(
            lambda v: v.trial_date_end and v.trial_date_end >= today
        )
        on_trial._set_employee_status("trial")
        (running - on_trial)._set_employee_status("active")

        # Contracts have ended
        ended = self.search(
            [
                ("contract_date_end", "!=", False),
                ("contract_date_end", "<", today),
            ]
        )
        for version in ended:
            version.start_separation(
                {
                    "name": version.contract_date_end,
                    "employee_id": version.employee_id.id,
                    "reason_id": self.env.ref(
                        "hr_employee_status.term_contract_end"
                    ).id,
                }
            )

        return True

    def _set_employee_status(self, status):
        """Set ``status`` on the employees of these versions.

        Employees whose separation is pending or done are left alone: their
        status belongs to the separation workflow.
        """
        employees = self.mapped("employee_id").filtered(
            lambda e: e.status not in ("separation", "inactive")
        )
        employees.write({"status": status})

        return True
