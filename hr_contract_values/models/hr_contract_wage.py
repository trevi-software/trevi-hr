# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class InitWage(models.Model):

    _name = "hr.contract.init.wage"
    _description = "Starting Wages"
    _sql_constraints = [
        (
            "unique_job_cinit",
            "UNIQUE(job_id,contract_init_id)",
            _(
                "A Job Position cannot be referenced more than once in"
                "a Contract Settings record."
            ),
        )
    ]

    job_id = fields.Many2one(string="Job", comodel_name="hr.job")
    starting_wage = fields.Monetary(required=True)
    currency_id = fields.Many2one("res.currency", "Currency")
    is_default = fields.Boolean(string="Use as Default", help="Use as default wage")
    contract_init_id = fields.Many2one(
        comodel_name="hr.contract.init", string="Contract Settings"
    )
    category_ids = fields.Many2many(
        string="Tags",
        comodel_name="hr.employee.category",
        relation="contract_init_category_rel",
        column1="contract_init_id",
        column2="category_id",
    )

    def unlink(self):

        data = self.read(["contract_init_id"])
        for d in data:
            if not d.get("contract_init_id", False):
                continue
            d2 = (
                self.env["hr.contract.init"]
                .browse(d["contract_init_id"][0])
                .read(["state"])
            )
            if d2["state"] in ["approve", "decline"]:
                raise UserError(
                    _(
                        "Error"
                        'You may not a delete a record that is not in a "Draft" state'
                    )
                )
        return super(InitWage, self).unlink()
