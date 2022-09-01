# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import math
from datetime import datetime

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
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
            "UNIQUE(company_id,name)",
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

    def _get_denominations(self):

        self.ensure_one()
        denominations = []
        smallest_note = 1

        # Get denominations for payroll currency
        # Arrange in order from largest value to smallest.
        #
        for denom in self.currency_id.denomination_ids:
            if float_compare(denom.ratio, 1.00, precision_digits=2) == 0:
                smallest_note = denom.value

            if len(denominations) == 0:
                denominations.append(denom.value)
                continue

            idx = 0
            last_idx = len(denominations) - 1
            for preexist_val in denominations:
                if denom.value > preexist_val:
                    denominations.insert(idx, denom.value)
                    break
                elif idx == last_idx:
                    denominations.append(denom.value)
                    break
                idx += 1
        return denominations, smallest_note

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

            denominations, smallest_note = register._get_denominations()

            denom_qty_list = dict.fromkeys(denominations, 0)
            cents_factor = float(smallest_note) / (
                len(denominations) and denominations[-1] or 1
            )
            for net in net_lines:
                cents, notes = math.modf(net)

                notes = int(notes)
                # XXX - rounding to 4 decimal places should work for most currencies... I hope
                cents = int(round(cents, 4) * cents_factor)
                for denom in denominations:
                    if notes >= denom:
                        denom_qty_list[denom] += int(notes / denom)
                        notes = (notes > 0) and (notes % denom) or 0

                    if notes == 0 and cents >= (denom * cents_factor):
                        cooked_denom = int(denom * cents_factor)
                        if cents >= cooked_denom:
                            denom_qty_list[denom] += cents / cooked_denom
                        elif denom == denominations[-1]:
                            denom_qty_list[denom] += cents / cents_factor
                            cents = 0
                        cents = cents % cooked_denom

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

        return


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
