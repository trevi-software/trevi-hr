# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import math
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class EnrollEmployee(models.TransientModel):

    _name = "hr.benefit.enroll.multi.employee"
    _description = "Employee Benefit Enrollment Form"

    benefit_id = fields.Many2one(
        string="Benefit",
        comodel_name="hr.benefit",
        required=True,
        default=lambda self: self._get_benefit(),
    )
    employee_ids = fields.Many2many(
        string="Employee",
        comodel_name="hr.employee",
        relation="hr_employee_benefit_rel",
        column1="employee_id",
        column2="benefit_id",
    )
    start_date = fields.Date(
        string="Enrollment Date", required=True, default=date.today()
    )
    end_date = fields.Date(string="Termination Date")
    advantage_override = fields.Boolean(string="Override Advantage")
    premium_override = fields.Boolean(string="Override Premium")
    advantage_amount = fields.Float(compute="_compute_amounts", digits="Account")
    premium_amount = fields.Float(compute="_compute_amounts", digits="Account")
    premium_total = fields.Float(compute="_compute_amounts", digits="Account")
    premium_installments = fields.Integer(
        compute="_compute_premium_installments", string="No. of Installments"
    )

    @api.model
    def _get_benefit(self):

        if self.env.context is None:
            self.env.context = {}
        return self.env.context.get("active_id", False)

    @api.depends("benefit_id")
    def _compute_amounts(self):

        for rec in self:
            res = {
                "advantage_amount": 0,
                "premium_amount": 0,
                "premium_total": 0,
            }

            if not rec.benefit_id or not rec.start_date:
                rec.write(res)

            dToday = rec.start_date
            adv = rec.benefit_id.get_latest_advantage(dToday)
            prm = rec.benefit_id.get_latest_premium(dToday)
            if adv is not None:
                if adv.type == "allowance":
                    res["advantage_amount"] = adv.allowance_amount

            if prm is not None:
                res["premium_amount"] = prm.amount
                res["premium_total"] = prm.total_amount

            rec.write(res)

    @api.depends("start_date", "premium_amount", "premium_total")
    def _compute_premium_installments(self):

        for rec in self:
            res = {"end_date": False, "premium_installments": 0}
            if rec.premium_amount == 0:
                rec.write(res)
                return

            installments = int(
                math.ceil(float(rec.premium_total) / float(rec.premium_amount))
            )
            if installments > 0:
                dEnd = rec.start_date + relativedelta(months=+installments)
                res["end_date"] = dEnd
            res["premium_installments"] = installments
            rec.write(res)

    def do_multi_enroll(self):

        if not self.benefit_id or len(self.employee_ids) == 0:
            return {"type": "ir.actions.act_window_close"}

        for employee in self.employee_ids:

            vals = {
                "benefit_id": self.benefit_id.id,
                "employee_id": employee.id,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "advantage_override": self.advantage_override,
                "premium_override": self.premium_override,
                "advantage_amount": self.advantage_amount,
                "premium_amount": self.premium_amount,
                "premium_total": self.premium_total,
            }
            pol_id = self.env["hr.benefit.policy"].create(vals)
            pol_id.state_open()

        return {"type": "ir.actions.act_window_close"}
