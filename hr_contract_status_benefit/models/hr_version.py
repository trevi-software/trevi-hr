# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class HrVersion(models.Model):
    """Link contract status with benefit policies.

    In Odoo 19 ``hr_contract`` was merged into ``hr`` and ``hr.contract`` was
    renamed to ``hr.version``. The trevi contract state machine
    (``draft``/``trial``/``open``/``pending_done``/``close``/``cancel`` plus
    ``kanban_state``) has been dropped in favour of the native ``active`` /
    ``is_current`` / ``is_past`` / ``is_future`` / ``is_in_contract`` flags:
    a contract is now "in effect" when its ``contract_date_start`` has been
    reached and its ``contract_date_end`` has not.

    The 18.0 module hooked two user/workflow steps of that state machine to
    activate the benefit policies an employee was enrolled in with the same
    start date as the contract:

    * ``hr.contract.update_state()``, the method the ``hr_contract`` "Update
      Contract State" cron called on newly started contracts. The 19.0 cron
      no longer exists; ``hr_contract_status`` runs its own cron which calls
      ``hr.version.update_status()``, so this module extends that method.
    * ``hr.contract.signal_confirm()``, the "Confirm" button of the contract
      form. That button (and its method) no longer exist, so the policies are
      activated by the daily cron alone once the contract is in effect.

    The "same start date" predicate is unchanged: a drafted policy is opened
    only when its ``start_date`` matches the contract's ``contract_date_start``.
    """

    _inherit = "hr.version"

    @api.model
    def update_status(self):
        res = super().update_status()

        # The contracts that are in effect today: started on or before today
        # and not (yet) ended. This is the native replacement of the 18.0
        # ``state = 'draft'`` + ``kanban_state = 'done'`` + ``date_start <=
        # today`` filter that used to select newly started contracts.
        today = fields.Date.context_today(self)
        versions = self.search(
            [
                ("employee_id", "!=", False),
                ("contract_date_start", "<=", today),
                "|",
                ("contract_date_end", "=", False),
                ("contract_date_end", ">=", today),
            ]
        )
        for version in versions:
            version.employee_id.benefit_policy_ids.filtered(
                lambda p, version=version: (
                    p.state == "draft" and p.start_date == version.contract_date_start
                )
            ).state_open()

        return res
