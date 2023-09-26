# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payslip Report",
    "summary": "Comprehensive payslip report by department.",
    "category": "Payroll",
    "version": "14.0.2.0.0",
    "author": "TREVI Software",
    "website": "https://github.com/trevi-software/trevi-hr",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "depends": [
        "payroll",
        "payroll_default_salary_rules",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/payslip_report_data.xml",
        "report/hr_payslip_report.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
