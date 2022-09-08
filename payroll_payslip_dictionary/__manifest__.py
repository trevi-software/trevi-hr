# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payslip Dictionary",
    "summary": "Dictionary of values that can be used in payslip calculations",
    "version": "14.0.1.2.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_contract",
        "hr_employee_seniority_months",
        "payroll",
        "payroll_default_salary_rules",
    ],
    "data": [
        "data/payroll_payslip_dictionary.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": ["demo/payroll_demo.xml"],
    "installable": True,
}
