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
        for worked_days_line in self.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in self.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(self.employee_id.id, {}, self.env)
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

    def compute_sheet(self):

        super(HrPayslip, self).compute_sheet()

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(
                    localdict, category.parent_id, amount
                )

            if category.code in localdict["categories"].dict:
                localdict["categories"].dict[category.code] += amount
            else:
                localdict["categories"].dict[category.code] = amount

            return localdict

        ExceptionRule = self.env["hr.payslip.exception.rule"]
        rule_ids = ExceptionRule.search([])
        rule_seq = []
        for rule in rule_ids:
            rule_seq.append((rule.id, rule.sequence))
        sorted_rule_ids = [id for id, sequence in sorted(rule_seq, key=lambda x: x[1])]
        sorted_rules = ExceptionRule.browse(sorted_rule_ids)

        for payslip in self:

            baselocaldict = self._get_baselocaldict_hook()
            employee = payslip.employee_id
            contract = employee.contract_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            localdict["result"] = None

            # Total the sum of the categories
            for line in payslip.details_by_salary_rule_category:
                localdict = _sum_salary_rule_category(
                    localdict, line.salary_rule_id.category_id, line.total
                )

            for rule in sorted_rules:
                for rule in sorted_rules:
                    if rule.satisfy_condition(localdict):
                        val = {
                            "name": rule.name,
                            "slip_id": payslip.id,
                            "rule_id": rule.id,
                        }
                        self.env["hr.payslip.exception"].create(val)

        return True
