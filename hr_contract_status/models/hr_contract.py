# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class HrContract(models.Model):

    _name = "hr.contract"
    _inherit = "hr.contract"

    trial_ending = fields.Boolean()
    state_ending = fields.Boolean()
    date_end_effective = fields.Date(string="Effective End Date", readonly=True)
    date_end_original = fields.Date(string="Original End Date", readonly=True)
    state = fields.Selection(
        selection_add=[
            ("draft",),
            ("trial", "Trial"),
            ("open",),
            ("close",),
            ("cancel",),
        ],
        ondelete={"trial": "set null"},
        default="draft",
        readonly=True,
    )

    department_id = fields.Many2one(
        compute="_compute_department",
        store=True,
        readonly=True,
    )

    # At contract end this field will hold the job_id, and the
    # job_id field will be set to null so that modules that
    # reference job_id don't include deactivated employees.
    # XXX ToDo: is it possible to change those references rather than using this hack?
    end_job_id = fields.Many2one(
        comodel_name="hr.job", string="Job Title", readonly=True
    )

    # The following are redefined again to make them editable only in certain states
    employee_id = fields.Many2one(
        readonly=True, states={"draft": [("readonly", False)]}
    )
    structure_type_id = fields.Many2one(
        readonly=True, states={"draft": [("readonly", False)]}
    )
    job_id = fields.Many2one(
        comodel_name="hr.job",
        compute=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        required=False,
        states={
            "draft": [("required", True)],
            "trial": [("required", True)],
            "open": [("required", True)],
        },
        tracking=True,
    )
    date_start = fields.Date(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    wage = fields.Monetary(
        readonly=True,
        states={
            "draft": [("readonly", False)],
            "trial": [("readonly", False)],
            "trial_ending": [("readonly", False)],
        },
    )

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
        return super(HrContract, self)._check_current_contract()

    def _track_subtype(self, init_values):
        self.ensure_one()
        if "state" in init_values:
            if self.state == "trial_ending":
                return self.env.ref("hr_contract_status.mt_alert_trial_ending")
            elif self.state == "contract_ending":
                return self.env.ref("hr_contract_status.mt_alert_contract_ending")
        return super(HrContract, self)._track_subtype(init_values)

    @api.model
    def update_state(self):

        # New contract with trial period
        self.search(
            [
                ("state", "=", "draft"),
                ("kanban_state", "=", "done"),
                ("date_start", "<=", fields.Date.to_string(date.today())),
                ("trial_date_end", ">=", fields.Date.to_string(date.today())),
            ]
        ).write({"state": "trial"})

        # Trial period is ending
        contracts = self.search(
            [
                ("state", "=", "trial"),
                (
                    "trial_date_end",
                    "<=",
                    fields.Date.to_string(date.today() + relativedelta(days=7)),
                ),
            ]
        )
        for contract in contracts:
            contract.kanban_state = "blocked"
            contract.trial_ending = True
            contract.activity_schedule(
                "mail.mail_activity_data_todo",
                contract.trial_date_end,
                _("The trial period of %s is about to end.", contract.employee_id.name),
                user_id=contract.hr_responsible_id.id or self.env.uid,
            )

        # Trial period has ended
        contracts = self.search(
            [
                ("state", "=", "trial"),
                (
                    "trial_date_end",
                    "<=",
                    fields.Date.to_string(date.today() - relativedelta(days=1)),
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
                "&",
                (
                    "date_end",
                    "<=",
                    fields.Date.to_string(date.today() + relativedelta(days=7)),
                ),
                (
                    "date_end",
                    ">=",
                    fields.Date.to_string(date.today() + relativedelta(days=1)),
                ),
                "&",
                (
                    "visa_expire",
                    "<=",
                    fields.Date.to_string(date.today() + relativedelta(days=60)),
                ),
                (
                    "visa_expire",
                    ">=",
                    fields.Date.to_string(date.today() + relativedelta(days=1)),
                ),
            ]
        ).write({"state_ending": True})

        # Contract has expired
        self.search(
            [
                ("state", "in", ["open", "close"]),
                ("state_ending", "=", True),
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
        ).write({"state_ending": False})

        return super(HrContract, self).update_state()

    def condition_trial_period(self):
        self.ensure_one()
        dToday = fields.Date.today()
        if not self.trial_date_end or (
            self.trial_date_end and self.trial_date_end < dToday
        ):
            return False
        return True

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
            if not c.date_end or c.date_end >= date.today():
                vals.update({"date_end": date.today()})
            c.write(vals)

    def write(self, vals):
        if vals.get("state") == "trial":
            self._assign_open_contract()
        return super(HrContract, self).write(vals)
