# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo import _, exceptions, fields, models


class HrPayslipAmendment(models.Model):

    _name = "hr.payslip.amendment"
    _inherit = ["mail.thread"]
    _description = "Pay Slip Amendment"

    date = fields.Date(
        default=lambda s: date.today(),
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    input_id = fields.Many2one(
        string="Salary Rule Input",
        comodel_name="hr.rule.input",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    amount = fields.Float(
        digits="Payroll",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)], "validate": [("readonly", False)]},
        help="The meaning of this field is dependent on the salary rule that uses it.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("validate", "Confirmed"),
            ("cancel", "Cancelled"),
            ("done", "Done"),
        ],
        default="draft",
        copy="False",
        required=True,
        readonly=True,
        tracking=True,
    )
    note = fields.Text(string="Memo")

    def name_get(self):

        res = []
        for rec in self:
            res.append((rec.id, "%s (%s)" % (rec.employee_id.name, rec.input_id.code)))

        return res

    def unlink(self):

        for psa in self:
            if psa.state in ["validate", "done"]:
                raise exceptions.UserError(
                    _("A Pay Slip Amendment that has been confirmed cannot be deleted!")
                )

        return super(HrPayslipAmendment, self).unlink()

    def do_validate(self):
        rset = self.filtered(lambda rec: rec.state == "draft")
        rset.state = "validate"

    def do_done(self):
        rset = self.filtered(lambda rec: rec.state == "validate")
        rset.state = "done"

    def do_cancel(self):
        rset = self.filtered(lambda rec: rec.state == "validate")
        rset.state = "cancel"

    def do_reset(self):
        rset = self.filtered(lambda rec: rec.state == "cancel")
        rset.state = "draft"
