# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models

from odoo.addons.payroll.models.hr_payslip import (
    BrowsableObject,
    InputLine,
    Payslips,
    WorkedDays,
)


class HrPayslip(models.Model):

    _inherit = "hr.payslip"

    def get_localdict(self, payslip, contract_ids):
        return {}

    def get_contractdict(self, payslip, contract, contract_ids):
        return {}

    # Patch _get_payslip_lines() from https://github.com/OCA/payroll/tree/14.0/payroll
    # This enables us to customize payroll computation lines with additional features.
    # Changes from original method:
    #   * Just before setting up the local dictionary call the method:
    #       get_localdict()
    #     This method returns a dictionary that will be available to the payslip
    #     rules in the key: 'dictionaries'
    #     For example:
    #       dictionaries.some_value
    #   * Just before running the salary rules for each contract call the method:
    #       get_contractdict()
    #     This method also returns a dictionary, but with contract dependent values.
    #     The values will be in the key 'this_contract'. i.e:
    #       this_contract.another_value
    #
    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
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

        # we keep a dict with the result because a value can be overwritten by
        # another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        contract_dict = {}
        blacklist = []
        payslip = self.env["hr.payslip"].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
        dictionaries = BrowsableObject(
            payslip.employee_id.id, self.get_localdict(payslip, contract_ids), self.env
        )
        this_contract = BrowsableObject(payslip.employee_id.id, contract_dict, self.env)

        baselocaldict = {
            "this_contract": this_contract,
            "dictionaries": dictionaries,
            "categories": categories,
            "rules": rules,
            "payslip": payslips,
            "worked_days": worked_days,
            "inputs": inputs,
        }

        # get the ids of the structures on the contracts and their parent id
        # as well
        contracts = self.env["hr.contract"].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = (
            self.env["hr.payroll.structure"].browse(structure_ids).get_all_rules()
        )
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env["hr.salary.rule"].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            contract_dict = self.get_contractdict(payslip, contract, contract_ids)
            baselocaldict["this_contract"] = BrowsableObject(
                payslip.employee_id.id, contract_dict, self.env
            )
            # baselocaldict["this_contract"].update({
            #     "contract": self.get_contractdict(payslip, contract, contract_ids)
            # })
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + "-" + str(contract.id)
                localdict["result"] = None
                localdict["result_qty"] = 1.0
                localdict["result_rate"] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = (
                        rule.code in localdict and localdict[rule.code] or 0.0
                    )
                    # set/overwrite the amount computed for this rule in the
                    # localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id, tot_rule - previous_amount
                    )
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        "salary_rule_id": rule.id,
                        "contract_id": contract.id,
                        "name": rule.name,
                        "code": rule.code,
                        "category_id": rule.category_id.id,
                        "sequence": rule.sequence,
                        "appears_on_payslip": rule.appears_on_payslip,
                        "condition_select": rule.condition_select,
                        "condition_python": rule.condition_python,
                        "condition_range": rule.condition_range,
                        "condition_range_min": rule.condition_range_min,
                        "condition_range_max": rule.condition_range_max,
                        "amount_select": rule.amount_select,
                        "amount_fix": rule.amount_fix,
                        "amount_python_compute": rule.amount_python_compute,
                        "amount_percentage": rule.amount_percentage,
                        "amount_percentage_base": rule.amount_percentage_base,
                        "register_id": rule.register_id.id,
                        "amount": amount,
                        "employee_id": contract.employee_id.id,
                        "quantity": qty,
                        "rate": rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

            baselocaldict["this_contract"] = None

        return list(result_dict.values())
