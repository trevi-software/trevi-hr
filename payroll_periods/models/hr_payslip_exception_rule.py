# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


# This is almost 100% lifted from hr_payroll/hr.salary.rule
# I ommitted the parts I don't use.
#
class HrPayslipExceptionRule(models.Model):

    _name = "hr.payslip.exception.rule"
    _description = "Rules describing pay slips in an abnormal state"
    _order = "sequence, code"

    def _generate_condition_str(self):
        conditions = """
# Available variables:
#----------------------
# payslip: object containing the payslips
# contract: hr.contract object
# categories: object containing sum of the amount of all rules belonging to a category
# worked_days: object containing the computed worked days
# inputs: object containing the computed inputs

# Note: returned value have to be set in the variable 'result'

result = categories.GROSS.amount > categories.NET.amount"""
        return conditions

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(
        required=True, help="Use to arrange calculation sequence", index=True
    )
    active = fields.Boolean(
        help="If the active field is set to false,"
        " it will allow you to hide the rule without removing it.",
        default=True,
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )
    condition_select = fields.Selection(
        string="Condition Based on",
        selection=[("none", "Always True"), ("python", "Python Expression")],
        default="none",
        required=True,
    )
    condition_python = fields.Text(
        string="Python Condition",
        readonly=False,
        help="The condition that triggers the exception.",
        default=_generate_condition_str,
    )
    severity = fields.Selection(
        selection=[("low", "Low"), ("medium", "Medium"), ("critical", "Critical")],
        default="low",
        required=True,
    )
    note = fields.Text(string="Description")

    def satisfy_condition(self, localdict):
        """
        @return: returns True if the given rule matches the condition for
        the given contract. Return False otherwise.
        """

        self.ensure_one()
        if self.condition_select == "none":
            return True
        else:  # python code
            try:
                safe_eval(self.condition_python, localdict, mode="exec", nocopy=True)
                return "result" in localdict and localdict["result"] or False
            except Exception:
                raise exceptions.UserError(
                    _("Error!")
                    + "\n"
                    + _(
                        "Wrong python condition defined for payroll exception rule %s (%s)."
                    )
                    % (self.name, self.code)
                )
