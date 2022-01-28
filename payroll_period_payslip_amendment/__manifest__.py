# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Periods and Payslip Amendments",
    "summary": "Link payslip amendments with a payroll period.",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "author": "TREVI Software",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "payroll_payslip_amendment",
        "payroll_period",
    ],
    "data": [
        "views/hr_payslip_amendment_view.xml",
    ],
    "installable": True,
}
