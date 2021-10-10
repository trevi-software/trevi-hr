# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAccrual(models.Model):

    _name = "hr.accrual"
    _description = "Accrual"

    name = fields.Char(required=True)
    holiday_status_id = fields.Many2one(string="Leave", comodel_name="hr.leave.type")
    line_ids = fields.One2many(
        string="Accrual Lines",
        comodel_name="hr.accrual.line",
        inverse_name="accrual_id",
        readonly=True,
    )

    def get_balance(self, employee_id, date=None):

        if date is None:
            date = fields.Date.today()

        res = 0.0
        self.env.cr.execute(
            """SELECT SUM(amount) from hr_accrual_line \
                           WHERE accrual_id in %s AND employee_id=%s AND date <= %s""",
            (tuple(self.ids), employee_id, date),
        )
        for row in self.env.cr.fetchall():
            res = row[0]

        return res

    def deposit(self, employee_id, amount, date, name=None):

        line_obj = self.env["hr.accrual.line"]

        res = []
        for accrual in self:

            lv = False
            if accrual.holiday_status_id:
                leave_allocation = {
                    "name": name is not None and name or "Allocation from Accrual",
                    "allocation_type": "regular",
                    "state": "draft",
                    "employee_id": employee_id,
                    "number_of_days": amount,
                    "holiday_status_id": accrual.holiday_status_id.id,
                    "from_accrual": True,
                }
                lv = self.env["hr.leave.allocation"].create(leave_allocation)
                lv.action_confirm()
                lv.action_validate()

            # Create accrual line
            #
            vals = {
                "date": date,
                "employee_id": employee_id,
                "amount": amount,
                "accrual_id": accrual.id,
                "leave_allocation_id": lv and lv.id or False,
            }
            res.append(line_obj.create(vals))

        return res


class HrAccrualLine(models.Model):

    _name = "hr.accrual.line"
    _description = "Accrual Line"
    _rec_name = "date"

    date = fields.Date(required=True, default=fields.Date.today())
    accrual_id = fields.Many2one(
        string="Accrual", comodel_name="hr.accrual", required=True
    )
    employee_id = fields.Many2one(
        string="Employee", comodel_name="hr.employee", required=True
    )
    leave_allocation_id = fields.Many2one("hr.leave.allocation")
    amount = fields.Float(digits="Accruals", required=True)
