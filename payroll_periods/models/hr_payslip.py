# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import logging

from odoo import fields, models

from odoo.addons.payroll.models.hr_payslip import (
    BrowsableObject,
    InputLine,
    Payslips,
    WorkedDays,
)

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = "hr.payslip"

    exception_ids = fields.One2many(
        string="Exceptions",
        comodel_name="hr.payslip.exception",
        inverse_name="slip_id",
        readonly=True,
    )

    def _get_baselocaldict_hook(self):
        """
        @return: returns a dictionary of objects for use in payslip exception rules
        """

        self.ensure_one()
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        categories_dict = self.get_categories_dict()
        for worked_days_line in self.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in self.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(self.employee_id.id, categories_dict, self.env)
        inputs = InputLine(self.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(self.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(self.employee_id.id, self, self.env)
        rules = BrowsableObject(self.employee_id.id, rules_dict, self.env)
        # XXX - breakout into separate module
        # temp_dict = {}
        # utils_dict = self.get_utilities_dict(self.contract_id, self)
        # for k, v in utils_dict.iteritems():
        #     k_obj = BrowsableObject(self.employee_id.id, v, self.env)
        #     temp_dict.update({k: k_obj})
        # utils = BrowsableObject(
        #   self.env, self.env.cr, self.env.user.id, self.employee_id.id, temp_dict)

        return {
            "categories": categories,
            "rules": rules,
            "payslip": payslips,
            "worked_days": worked_days,
            "inputs": inputs,
            # 'utils': utils,
        }

    def get_categories_dict(self):
        def _sum_salary_rule_category(_dict, category, amount):
            if category.parent_id:
                _dict = _sum_salary_rule_category(_dict, category.parent_id, amount)

            if category.code in _dict.keys():
                _dict[category.code] += amount
            else:
                _dict[category.code] = amount

            return _dict

        self.ensure_one()

        # Get all the rules for all the payroll structures associated
        # with all the contracts for this employee for this period
        #
        contracts = self.employee_id._get_contracts(
            date_from=self.date_from, date_to=self.date_to
        )
        structure_ids = contracts.get_all_structures()
        tupleList = (
            self.env["hr.payroll.structure"].browse(structure_ids).get_all_rules()
        )
        rule_ids = [i for i, _s in tupleList]
        rules = self.env["hr.salary.rule"].browse(rule_ids).sorted("sequence")

        # Setup categories dict with all possible categories
        #
        categories = {}
        for rule in rules:
            if rule.category_id.code not in categories.keys():
                categories.update({rule.category_id.code: 0})
        if not categories:
            _logger.warning(
                f"Payslip {self.number}: could not get salary rule categories."
            )
            return categories

        # Populate the dict with the sum of all the salary lines for that
        # category and its children
        for line in self.line_ids:
            idCateg = line.salary_rule_id.category_id.code
            prev_amount = 0
            if not fields.Float.is_zero(categories[idCateg], precision_rounding=2):
                prev_amount = categories[idCateg]
            categories = _sum_salary_rule_category(
                categories, line.salary_rule_id.category_id, line.total - prev_amount
            )

        return categories

    def compute_sheet(self):

        res = super(HrPayslip, self).compute_sheet()

        sorted_rules = (
            self.env["hr.payslip.exception.rule"].search([]).sorted("sequence")
        )

        for payslip in self:

            baselocaldict = payslip._get_baselocaldict_hook()
            employee = payslip.employee_id
            contract = employee.contract_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)

            for rule in sorted_rules:
                localdict["result"] = False
                if rule.satisfy_condition(localdict):
                    val = {
                        "name": rule.name,
                        "slip_id": payslip.id,
                        "rule_id": rule.id,
                    }
                    payslip.env["hr.payslip.exception"].create(val)

        return res
