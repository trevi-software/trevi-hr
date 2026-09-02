# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models
from odoo.tools.translate import LazyTranslate

_lt = LazyTranslate(__name__)
from odoo.exceptions import UserError


class InitWage(models.Model):
    _name = "hr.contract.init.wage"
    _description = "Starting Wages"
    _sql_constraints = [  # noqa: RUF012
        (
            "unique_job_cinit",
            "UNIQUE(job_id,contract_init_id)",
            _lt(
                "A Job Position cannot be referenced more than once in "
                "a Contract Settings record."
            ),
        )
    ]

    job_id = fields.Many2one(comodel_name="hr.job")
    starting_wage = fields.Monetary(required=True)
    currency_id = fields.Many2one("res.currency")
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
                .read(["locked"])
            )
            if d2["locked"]:
                raise UserError(
                    self.env._(
                        "Error"
                        "You may not delete a record that is locked. Unlock it first."
                    )
                )
        return super().unlink()
