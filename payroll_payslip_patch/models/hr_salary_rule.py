# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    # Override parent method to fix eval of 'amount_python_compute'
    #
    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to
                          compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity
                 and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == "fix":
            try:
                return (
                    self.amount_fix,
                    float(safe_eval(self.quantity, localdict)),
                    100.0,
                )
            except Exception:
                raise UserError(
                    _("Wrong quantity defined for salary rule %s (%s).")
                    % (self.name, self.code)
                )
        elif self.amount_select == "percentage":
            try:
                return (
                    float(safe_eval(self.amount_percentage_base, localdict)),
                    float(safe_eval(self.quantity, localdict)),
                    self.amount_percentage,
                )
            except Exception:
                raise UserError(
                    _(
                        "Wrong percentage base or quantity defined for salary "
                        "rule %s (%s)."
                    )
                    % (self.name, self.code)
                )
        else:
            try:
                safe_eval(
                    self.amount_python_compute, localdict, mode="exec", nocopy=True
                )
                result_qty = 1.0
                result_rate = 100.0
                if "result_qty" in localdict:
                    result_qty = localdict["result_qty"]
                if "result_rate" in localdict:
                    result_rate = localdict["result_rate"]
                return (
                    float(localdict["result"]),
                    float(result_qty),
                    float(result_rate),
                )
            except Exception:
                raise UserError(
                    _("Wrong python code defined for salary rule %s (%s).")
                    % (self.name, self.code)
                )
