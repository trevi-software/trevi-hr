# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import api, fields, models
from odoo.tools.translate import _


class HrPayrollRun(models.Model):

    _name = "hr.payslip.run"
    _inherit = "hr.payslip.run"

    register_id = fields.Many2one(comodel_name="hr.payroll.register", string="Register")
    department_ids = fields.Many2many(
        comodel_name="hr.department",
        relation="hr_payroll_register_department_rel",
        column1="register_id",
        column2="department_id",
        string="Department",
    )


class HrPayrollRegister(models.Model):

    _name = "hr.payroll.register"
    _description = "Payroll Register"
    _sql_constraints = [
        (
            "unique_name",
            "CHECK(1=1)",
            _("Payroll Register description must be unique per company."),
        )
    ]

    @api.model
    def _get_default_name(self):

        nMonth = datetime.now().strftime("%B")
        year = datetime.now().year
        name = _("Payroll for the Month of %s %s" % (nMonth, year))
        return name

    name = fields.Char(string="Description", required=True, default=_get_default_name)
    period_name = fields.Char()
    state = fields.Selection(
        string="Status",
        selection=[("draft", "Draft"), ("close", "Close")],
        index=True,
        default="draft",
        readonly=True,
    )
    date_start = fields.Datetime(
        string="Date From",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_end = fields.Datetime(
        string="Date To",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    run_ids = fields.One2many(
        comodel_name="hr.payslip.run",
        inverse_name="register_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )
    denomination_ids = fields.One2many(
        string="Denomination Quantitiess",
        comodel_name="hr.payroll.register.denominations",
        inverse_name="register_id",
        readonly=True,
    )
    exact_change = fields.Monetary(
        string="Net Amount", compute="_compute_change", readonly=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        "Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    def _compute_change(self):

        res = 0
        for reg in self:
            for den in reg.denomination_ids:
                res += den.denomination * den.denomination_qty
            reg.exact_change = res

    def name_get(self):
        res = []
        for rec in self:
            if not rec.period_name or rec.period_name in rec.name:
                res.append((rec.id, f"{rec.name}"))
            else:
                res.append((rec.id, f"{rec.period_name} {rec.name}"))
        return res

    def action_delete_runs(self):

        PayslipRun = self.env["hr.payslip.run"]
        payslip_run_ids = PayslipRun.search([("register_id", "in", self.ids)])
        payslip_run_ids.unlink()
        return True

    @api.model
    def get_net_payslip_lines_domain(self, run_ids):

        return [
            ("slip_id.payslip_run_id", "in", run_ids.ids),
            ("salary_rule_id.code", "=", "NET"),
        ]

    @api.model
    def get_net_payslip_lines(self, run_ids):

        net_lines = []
        PayslipLine = self.env["hr.payslip.line"]
        slip_line_ids = PayslipLine.search(self.get_net_payslip_lines_domain(run_ids))
        for line in slip_line_ids:
            net_lines.append(line.total)

        return net_lines

    def set_denominations(self):

        Denominations = self.env["hr.payroll.register.denominations"]
        for register in self:
            if len(register.run_ids) == 0:
                return

            # Remove current denomination count
            den_ids = Denominations.search([("register_id", "=", register.id)])
            den_ids.unlink()

            # Get list of all 'NET' payslip lines
            #
            net_lines = self.get_net_payslip_lines(register.run_ids)
            if len(net_lines) == 0:
                return

            currency = self.currency_id
            denominations, smallest_note = currency.get_denomination_list()
            denom_qty_list = dict.fromkeys(denominations, 0)
            for net in net_lines:
                denominations_list = currency.get_denominations_from_amount(net)
                for line in denominations_list:
                    denom_qty_list[line["name"]] += line["qty"]

            exact_change = 0.0
            for k, v in denom_qty_list.items():
                Denominations.create(
                    {
                        "register_id": register.id,
                        "denomination": k,
                        "denomination_qty": v,
                    }
                )
                exact_change += k * v

            register.exact_change = exact_change


class HrPayrollRegisterDenominations(models.Model):

    _name = "hr.payroll.register.denominations"
    _description = "Exact denomination amounts for entire payroll register"
    _order = "denomination"

    register_id = fields.Many2one(
        string="Payroll Register",
        comodel_name="hr.payroll.register",
        required=True,
        ondelete="cascade",
    )
    denomination = fields.Float(digits=(12, 6), required=True)
    denomination_qty = fields.Integer(string="Quantity")
