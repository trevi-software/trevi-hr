# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class InfractionBatch(models.TransientModel):
    _name = "hr.infraction.batch"
    _description = "Generate mass infraction incidents"

    employee_ids = fields.Many2many(
        string="Employees",
        comodel_name="hr.employee",
        relation="hr_employee_infraction_batch_rel",
        column1="infraction_id",
        column2="employee_id",
    )
    category_id = fields.Many2one(
        string="Infraction Category",
        comodel_name="hr.infraction.category",
        required=True,
    )
    name = fields.Char(string="Subject")
    date = fields.Date(default=fields.Date.today(), required=True)
    memo = fields.Text(string="Description")

    @api.onchange("category_id")
    def onchange_category(self):

        if self.category_id:
            self.name = self.category_id.name
        else:
            self.name = False

    def create_infractions(self):

        if not self.employee_ids:
            raise UserError(
                _(
                    "Warning !\n"
                    "You must select at least one employee to generate wage adjustments."
                )
            )

        Infraction = self.env["hr.infraction"]
        infraction_ids = []
        vals = {
            "name": self.name,
            "category_id": self.category_id.id,
            "date": self.date,
            "memo": self.memo,
            "employee_id": False,
        }

        for employee in self.employee_ids:
            vals["employee_id"] = employee.id
            infraction_ids.append(Infraction.create(vals))

        for infraction in infraction_ids:
            infraction.action_confirm()

        return {"type": "ir.actions.act_window_close"}
