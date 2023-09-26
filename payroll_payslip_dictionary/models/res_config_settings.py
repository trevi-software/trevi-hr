# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    work_days_code_max = fields.Char(
        config_parameter="payroll_payslip_dictionary.work_days_code_max"
    )
    working_days_calculation = fields.Selection(
        selection=[
            ("calendar", "Calendar month"),
            ("resource_calendar", "Resource calendar"),
            ("defaults", "Defaults"),
        ],
        help="""How to calculate the working days in a payslip.
        Calendar - based on calendar month.
        Resource calendar - based on the contract's resource calendar.
        Defaults - Use the default values defined here.
        """,
        config_parameter="payroll_payslip_dictionary.working_days_calculation",
    )
    daily_max_regular_hours = fields.Integer(
        config_parameter="payroll_payslip_dictionary.daily_max_regular_hours"
    )
    weekly_max_regular_hours = fields.Integer(
        config_parameter="payroll_payslip_dictionary.weekly_max_regular_hours"
    )
    monthly_max_working_days = fields.Integer(
        config_parameter="payroll_payslip_dictionary.monthly_max_working_days"
    )
