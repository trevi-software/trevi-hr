# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class DepartmentSelection(models.TransientModel):

    _name = "resource.schedule.validate.departments"
    _description = "Department Selection for Validation"

    department_ids = fields.Many2many(
        string="Departments",
        comodel_name="hr.department",
    )

    def view_schedules(self):

        data = self.read()[0]
        return {
            "view_mode": "tree,form",
            "res_model": "resource.schedule.shift",
            "domain": [
                ("department_id", "in", data["department_ids"]),
                ("published", "=", False),
            ],
            "type": "ir.actions.act_window",
            "target": "new",
            "nodestroy": True,
            "context": self.env.context,
        }

    def do_validate(self):

        sched_ids = self.env["resource.schedule.shift"].search(
            [("department_id", "in", self.department_ids.ids)]
        )
        sched_ids.publish()

        return {"type": "ir.actions.act_window_close"}
