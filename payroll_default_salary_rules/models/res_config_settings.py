# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    categ_info = fields.Char(
        string="Informational Categ.",
        config_parameter="payroll_default_salary_rules.categ_info",
    )

    categ_ee_contribution = fields.Char(
        string="Employee Contribution Categ.",
        config_parameter="payroll_default_salary_rules.categ_ee_contribution",
    )

    categ_er_contribution = fields.Char(
        string="Employer Contribution Categ.",
        config_parameter="payroll_default_salary_rules.categ_er_contribution",
    )

    categ_basic = fields.Char(
        string="Basic Categ.",
        config_parameter="payroll_default_salary_rules.categ_basic",
    )

    categ_ot = fields.Char(
        string="OT Categ.", config_parameter="payroll_default_salary_rules.categ_ot"
    )

    categ_allowance = fields.Char(
        string="Allowance Categ.",
        config_parameter="payroll_default_salary_rules.categ_allowance",
    )

    categ_taxexempt = fields.Char(
        string="Tax Exempt Categ.",
        config_parameter="payroll_default_salary_rules.categ_taxexempt",
    )

    categ_taxable = fields.Char(
        string="Taxable Gross Categ.",
        config_parameter="payroll_default_salary_rules.categ_taxable",
    )

    categ_gross = fields.Char(
        string="Gross Categ.",
        config_parameter="payroll_default_salary_rules.categ_gross",
    )

    categ_payroll_tax_ee = fields.Char(
        string="EE Payroll Tax Categ.",
        config_parameter="payroll_default_salary_rules.categ_payroll_tax_ee",
    )

    categ_payroll_tax_er = fields.Char(
        string="ER Payroll Tax Categ.",
        config_parameter="payroll_default_salary_rules.categ_payroll_tax_er",
    )

    categ_income_tax = fields.Char(
        string="Income Tax Categ.",
        config_parameter="payroll_default_salary_rules.categ_income_tax",
    )

    categ_deduction = fields.Char(
        string="Deduction Categ.",
        config_parameter="payroll_default_salary_rules.categ_deduction",
    )

    categ_net = fields.Char(
        string="Net Categ.", config_parameter="payroll_default_salary_rules.categ_net"
    )

    rule_gross = fields.Char(
        string="Gross Rule", config_parameter="payroll_default_salary_rules.rule_gross"
    )

    rule_net = fields.Char(
        string="Net Rule", config_parameter="payroll_default_salary_rules.rule_net"
    )
