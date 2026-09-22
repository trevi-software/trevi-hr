# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrContract(models.Model):
    _name = "hr.contract"
    _inherit = "hr.contract"

    trial_ending = fields.Boolean()
    state_ending = fields.Boolean()
    date_end_effective = fields.Date(string="Effective End Date")
    date_end_original = fields.Date(string="Original End Date")
    state = fields.Selection(
        selection_add=[
            ("draft",),
            ("trial", "Trial"),
            ("open",),
            ("pending_done", "Pending Separation"),
            ("close",),
            ("cancel",),
        ],
        ondelete={"trial": "set null"},
        default="draft",
    )

    department_id = fields.Many2one(
        comodel_name="hr.department",
        compute="_compute_department",
        store=True,
    )

    # At contract end this field will hold the job_id, and the
    # job_id field will be set to null so that modules that
    # reference job_id don't include deactivated employees.
    # XXX ToDo: is it possible to change those references rather than using this hack?
    end_job_id = fields.Many2one(comodel_name="hr.job", string="Last Job Position")

    @api.depends("job_id")
    def _compute_department(self):
        for contract in self:
            contract.department_id = contract.job_id.department_id

    # Override from inherited model. job_id and department_id in hr.employee should be
    # calculated from the contract.
    #
    @api.depends("employee_id")
    def _compute_employee_contract(self):
        for contract in self.filtered("employee_id"):
            contract.resource_calendar_id = contract.employee_id.resource_calendar_id
            contract.company_id = contract.employee_id.company_id

    @api.constrains("employee_id", "state", "kanban_state", "date_start", "date_end")
    def _check_current_contract(self):

        allow = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_contract_status.concurrent_contracts", False)
        )
        if allow:
            return
        return super()._check_current_contract()

    def write(self, vals):
        res = super().write(vals)
        if vals.get("state") == "trial":
            self._assign_open_contract()
        return res

    def _track_subtype(self, init_values):
        self.ensure_one()
        if "state" in init_values:
            if self.state == "trial" and self.trial_ending:
                return self.env.ref("hr_contract_status.mt_alert_trial_ending")
            elif self.state_ending:
                return self.env.ref("hr_contract_status.mt_alert_contract_ending")
        return super()._track_subtype(init_values)

    @api.model
    def update_state(self):

        # New contract with trial period
        self.search(
            [
                ("state", "=", "draft"),
                ("kanban_state", "=", "done"),
                ("date_start", "<=", date.today().strftime("%Y-%m-%d")),  # noqa: DTZ011
                ("trial_date_end", ">=", date.today().strftime("%Y-%m-%d")),  # noqa: DTZ011
            ]
        ).write({"state": "trial"})

        # Trial period is ending
        contracts = self.search(
            [
                ("state", "=", "trial"),
                (
                    "trial_date_end",
                    "<=",
                    (date.today() + relativedelta(days=7)).strftime("%Y-%m-%d"),  # noqa: DTZ011
                ),
            ]
        )
        for contract in contracts:
            contract.kanban_state = "blocked"
            contract.trial_ending = True
            contract.activity_schedule(
                "mail.mail_activity_data_todo",
                contract.trial_date_end,
                self.env._(
                    "The trial period of %s is about to end.", contract.employee_id.name
                ),
                user_id=contract.hr_responsible_id.id or self.env.uid,
            )

        # Trial period has ended
        contracts = self.search(
            [
                ("state", "=", "trial"),
                (
                    "trial_date_end",
                    "<=",
                    (date.today() - relativedelta(days=1)).strftime("%Y-%m-%d"),  # noqa: DTZ011
                ),
            ]
        )
        for contract in contracts:
            contract.state = "open"
            contract.kanban_state = "normal"
            contract.trial_ending = False

        # Contract is expiring
        self.search(
            [
                ("state", "=", "open"),
                ("kanban_state", "!=", "blocked"),
                "|",
                (
                    "date_end",
                    "<=",
                    (date.today() + relativedelta(days=7)).strftime("%Y-%m-%d"),  # noqa: DTZ011
                ),
                (
                    "date_end",
                    ">=",
                    (date.today() + relativedelta(days=1)).strftime("%Y-%m-%d"),  # noqa: DTZ011
                ),
            ]
        ).write({"state_ending": True})

        # Contract has expired
        self.search(
            [
                ("state", "in", ["open", "close"]),
                (
                    "date_end",
                    "<=",
                    date.today().strftime("%Y-%m-%d"),  # noqa: DTZ011
                ),
            ]
        ).write({"state_ending": False})

        return super().update_state()

    def condition_trial_period(self):
        self.ensure_one()
        dToday = fields.Date.today()

        return bool(self.trial_date_end and self.trial_date_end >= dToday)

    def signal_confirm(self):
        for rec in self:
            if rec.kanban_state == "done":
                rec.kanban_state = "normal"
            if rec.condition_trial_period():
                rec.state = "trial"
            else:
                rec.state = "open"

    def signal_close(self):
        for c in self:
            vals = {"state": "close"}
            if not c.date_end or c.date_end >= date.today():  # noqa: DTZ011
                vals.update({"date_end": date.today()})  # noqa: DTZ011
            c.write(vals)

    def signal_reactivate(self):
        for c in self:
            vals = {"state": "trial" if c.condition_trial_period() else "open"}
            if c.date_end and c.date_end <= date.today():  # noqa: DTZ011
                vals.update({"date_end": False})
            c.write(vals)
