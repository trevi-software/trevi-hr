# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import str2bool

CONCURRENT_CONTRACTS_PARAM = "hr_contract_status.concurrent_contracts"
NOTICE_PERIOD_DAYS = 7


class HrVersion(models.Model):
    """Employee contract status.

    In Odoo 19 ``hr_contract`` was merged into ``hr`` and ``hr.contract`` was
    renamed to ``hr.version``. The trevi contract state machine
    (``draft``/``trial``/``open``/``pending_done``/``close``/``cancel`` plus
    ``kanban_state``) has been dropped: a version is described by the native
    ``active``, ``is_current``/``is_past``/``is_future``/``is_in_contract``
    flags and by its ``contract_date_start`` / ``contract_date_end`` /
    ``trial_date_end`` / ``date_version`` dates.

    What is left of the module is the "contract is about to end" notification:
    the two flags below are refreshed by :meth:`update_status`, which is run by
    this module's cron (see ``data/hr_version_data.xml``).
    """

    _inherit = "hr.version"

    trial_ending = fields.Boolean(tracking=True)
    state_ending = fields.Boolean(tracking=True)
    date_end_effective = fields.Date(string="Effective End Date")
    date_end_original = fields.Date(string="Original End Date")

    # A contract's department is the one of the job it is attached to.
    department_id = fields.Many2one(
        comodel_name="hr.department",
        compute="_compute_department",
        store=True,
        readonly=False,
        check_company=True,
        tracking=True,
        index=True,
    )

    @api.depends("job_id")
    def _compute_department(self):
        for version in self:
            version.department_id = version.job_id.department_id

    @api.constrains("employee_id", "contract_date_start", "contract_date_end")
    def _check_dates(self):
        # ``hr.version._check_dates`` rejects versions whose contract periods
        # overlap. Trevi allows them when the "Allow concurrent contracts"
        # setting is enabled (this replaces the old ``_check_current_contract``
        # override, which keyed on the dropped ``state``/``kanban_state``).
        allow = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(CONCURRENT_CONTRACTS_PARAM, False)
        )
        if str2bool(allow):
            return
        return super()._check_dates()

    def _track_subtype(self, initial_values):
        self.ensure_one()
        if (
            "trial_ending" in initial_values
            and self.trial_ending
            and not initial_values["trial_ending"]
        ):
            return self.env.ref("hr_contract_status.mt_alert_trial_ending")
        if (
            "state_ending" in initial_values
            and self.state_ending
            and not initial_values["state_ending"]
        ):
            return self.env.ref("hr_contract_status.mt_alert_contract_ending")
        return super()._track_subtype(initial_values)

    @api.model
    def update_status(self):
        """Flag the versions whose trial period or contract is about to end.

        In 18.0 this was an override of ``hr.contract.update_state()``, which
        ``hr_contract``'s "Update Contract State" cron used to call. That cron
        does not exist in 19.0, so the module owns it now.
        """
        today = fields.Date.context_today(self)
        notice_date = today + relativedelta(days=NOTICE_PERIOD_DAYS)

        trials_ending = self.search(
            [
                ("trial_ending", "=", False),
                ("trial_date_end", ">=", today),
                ("trial_date_end", "<=", notice_date),
            ]
        )
        for version in trials_ending:
            version.activity_schedule(
                "mail.mail_activity_data_todo",
                version.trial_date_end,
                self.env._(
                    "The trial period of %s is about to end.",
                    version.employee_id.name,
                ),
                user_id=version.hr_responsible_id.id or self.env.uid,
            )
        trials_ending.trial_ending = True

        self.search(
            [
                ("state_ending", "=", False),
                ("contract_date_end", ">=", today),
                ("contract_date_end", "<=", notice_date),
            ]
        ).state_ending = True

        self._clear_ending("trial_ending", "trial_date_end", today, notice_date)
        self._clear_ending("state_ending", "contract_date_end", today, notice_date)

    @api.model
    def _clear_ending(self, flag_field, date_field, today, notice_date):
        """Reset the flag of the versions that left the notice period."""
        self.search(
            [
                (flag_field, "=", True),
                "|",
                "|",
                (date_field, "=", False),
                (date_field, "<", today),
                (date_field, ">", notice_date),
            ]
        ).write({flag_field: False})
