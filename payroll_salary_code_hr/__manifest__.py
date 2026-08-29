# Copyright (C) 2025 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Salary Code - HR Link",
    "summary": "Link payroll salary codes to employee contracts.",
    "version": "18.0.1.0.0",
    "category": "Payroll",
    "author": "TREVI Software",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_contract",
        "payroll_salary_code",
    ],
    "data": [
        "views/hr_contract_views.xml",
    ],
    "installable": True,
    "application": False,
}
