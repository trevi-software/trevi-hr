# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

ACTION_TYPE_SELECTION = [
    ("warning_verbal", "Verbal Warning"),
    ("warning_letter", "Written Warning"),
    ("transfer", "Transfer"),
    ("suspension", "Suspension"),
    ("dismissal", "Dismissal"),
]


class HrInfractionCategory(models.Model):
    _name = "hr.infraction.category"
    _description = "Infraction Type"

    name = fields.Char(required=True)
    code = fields.Char(required=True)


class HrInfraction(models.Model):
    _name = "hr.infraction"
    _description = "Infraction"
    _inherit = ["mail.thread"]

    name = fields.Char(
        string="Subject",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date = fields.Date(
        required=True,
        readonly=True,
        default=fields.Date.today(),
        states={"draft": [("readonly", False)]},
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    category_id = fields.Many2one(
        string="Category",
        comodel_name="hr.infraction.category",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    action_ids = fields.One2many(
        string="Actions",
        comodel_name="hr.infraction.action",
        inverse_name="infraction_id",
        readonly=True,
    )
    manager_id = fields.Many2one(
        string="Issued By",
        comodel_name="hr.employee",
        related="employee_id.parent_id",
        readonly=True,
        store=True,
    )
    department_id = fields.Many2one(
        string="Department",
        comodel_name="hr.department",
        related="employee_id.department_id",
        readonly=True,
        store=True,
    )
    memo = fields.Text(
        string="Description", readonly=True, states={"draft": [("readonly", False)]}
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("action", "Actioned"),
            ("noaction", "No Action"),
        ],
        tracking=True,
        default="draft",
        readonly=True,
    )

    @api.model
    def _is_valid_state_change(self, start, end):
        _valid_state_changes = [
            ("draft", "confirm"),
            ("confirm", "action"),
            ("confirm", "noaction"),
        ]
        return (start, end) in _valid_state_changes

    def _check_state(self, state, group):

        for infraction in self:
            if not self._is_valid_state_change(infraction.state, state):
                raise UserError(_("Invalid State Change"))
            elif not self.user_has_groups(group):
                raise AccessError(_("You don't have permission to take this action."))
        return True

    def action_confirm(self):

        if self._check_state("confirm", "hr_infraction.group_hr_infraction_entry"):
            self.state = "confirm"

    def action_action(self):

        if self._check_state("action", "hr_infraction.group_hr_infraction_approve"):
            self.state = "action"

    def action_noaction(self):

        if self._check_state("noaction", "hr_infraction.group_hr_infraction_approve"):
            self.state = "noaction"

    def _track_subtype(self, init_values):

        self.ensure_one()
        if "state" in init_values:
            if self.state == "confirm":
                return self.env.ref("hr_infraction.mt_alert_infraction_confirmed")
            elif self.state == "action":
                return self.env.ref("hr_infraction.mt_alert_infraction_action")
            elif self.state == "noaction":
                return self.env.ref("hr_infraction.mt_alert_infraction_noaction")

        return super(HrInfraction, self)._track_subtype(init_values)

    def unlink(self):

        for infraction in self:
            if infraction.state not in ["draft"]:
                raise UserError(
                    _(
                        "Error\n"
                        "Infractions that have progressed beyond 'Draft'"
                        " state may not be removed."
                    )
                )

        return super(HrInfraction, self).unlink()

    @api.onchange("category_id")
    def onchange_category(self):

        if self.category_id:
            self.name = self.category_id.name
        else:
            self.name = False

    @api.onchange("employee_id")
    def onchange_employee(self):

        if self.employee_id and self.employee_id.parent_id:
            self.manager_id = self.employee_id.parent_id
        else:
            self.manager_id = False


class HrInfractionAction(models.Model):
    _name = "hr.infraction.action"
    _description = "Action Based on Infraction"
    _rec_name = "type"

    infraction_id = fields.Many2one(
        string="Infraction",
        comodel_name="hr.infraction",
        ondelete="cascade",
        required=True,
        readonly=True,
    )
    type = fields.Selection(selection=ACTION_TYPE_SELECTION, required=True)
    memo = fields.Text(string="Notes")
    employee_id = fields.Many2one(
        string="Employee",
        related="infraction_id.employee_id",
        store=True,
        comodel_name="hr.employee",
        readonly=True,
    )
    warning_id = fields.Many2one(
        string="Warning", comodel_name="hr.infraction.warning", readonly=True
    )
    transfer_id = fields.Many2one(
        string="Transfer", comodel_name="hr.department.transfer", readonly=True
    )

    def unlink(self):

        for action in self:
            if action.infraction_id.state not in ["draft"]:
                raise UserError(
                    _(
                        "Error\n"
                        "Actions belonging to Infractions not in 'Draft'"
                        " state may not be removed."
                    )
                )

        return super(HrInfractionAction, self).unlink()


class HrWarning(models.Model):
    _name = "hr.infraction.warning"
    _description = "Employee Warning"

    name = fields.Char(string="Subject")
    date = fields.Date(string="Date Issued", default=fields.Date.today())
    type = fields.Selection(
        selection=[("verbal", "Verbal"), ("written", "Written")],
        default="written",
        required=True,
    )
    action_id = fields.Many2one(
        string="Action",
        comodel_name="hr.infraction.action",
        ondelete="cascade",
        readonly=True,
    )
    infraction_id = fields.Many2one(
        string="Infraction",
        comodel_name="hr.infraction",
        related="action_id.infraction_id",
        readonly=True,
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        related="infraction_id.employee_id",
        readonly=True,
    )

    def unlink(self):

        for warning in self:
            if warning.action_id and warning.action_id.infraction_id.state not in [
                "draft"
            ]:
                raise UserError(
                    _(
                        "Error\n"
                        "Warnings attached to Infractions not in 'Draft'"
                        " state may not be removed."
                    )
                )

        return super(HrWarning, self).unlink()


class HrEmployee(models.Model):
    _name = "hr.employee"
    _inherit = "hr.employee"

    infraction_ids = fields.One2many(
        string="Infractions",
        comodel_name="hr.infraction",
        inverse_name="employee_id",
        readonly=True,
    )
    infraction_action_ids = fields.One2many(
        string="Disciplinary Actions",
        comodel_name="hr.infraction.action",
        inverse_name="employee_id",
        readonly=True,
    )
