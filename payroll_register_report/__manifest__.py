# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Register Report",
    "summary": "List payslips with salary categories by batch.",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "license": "AGPL-3",
    "author": "TREVI Software",
    "website": "https://github.com/trevi-software/trevi-hr",
    "images": ["static/src/img/main_screenshot.png"],
    "depends": [
        "payroll",
        "payroll_payslip_dictionary",
        "payroll_period_processing",
        "payroll_register",
    ],
    "data": [
        "report/report.xml",
        "report/report_payroll_register.xml",
    ],
    "installable": True,
}
