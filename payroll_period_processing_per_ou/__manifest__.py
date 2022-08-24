# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Period Processing per Operating Unit",
    "summary": "For each period process only those payslips that belong to the OU.",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "author": "TREVI Software",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "payroll_operating_unit",
        "payroll_period_per_ou",
        "payroll_period_processing",
        "payroll_register",
    ],
    "data": [
        "security/ir_rule.xml",
    ],
    "installable": True,
}
