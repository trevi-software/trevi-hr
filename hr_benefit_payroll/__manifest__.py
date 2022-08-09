# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Benefits Payroll",
    "summary": "Access benefits in payroll through salary rules.",
    "version": "14.0.1.0.1",
    "category": "Payroll",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_benefit",
        "payroll",
        "payroll_payslip_dictionary",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/benefit_view.xml",
        "views/benefit_policy_view.xml",
        "views/benefit_premium_payment_view.xml",
        "views/hr_employee_view.xml",
        "views/hr_payslip_view.xml",
        "views/hr_salary_rule_view.xml",
    ],
    "installable": True,
}
