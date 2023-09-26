# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HR Data Import",
    "summary": "Import HR data from another system using Excel",
    "version": "15.0.1.0.0",
    "category": "Human Resources",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_accrual_bank",
        "hr_benefit",
        "hr_contract_reference",
        "hr_contract_status",
        "hr_contract_type",
        "hr_employee_seniority_months",
        "hr_employee_status",
        "hr_holidays_public",
        "payroll_default_salary_rules",
        "payroll_periods",
        "payroll_policy_absence",
        "payroll_policy_accrual",
        "payroll_policy_group",
        "payroll_policy_presence",
        "payroll_policy_ot",
        "payroll_policy_rounding",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/menus.xml",
        "views/hr_data_import_employee_views.xml",
        "views/hr_employee_view.xml",
    ],
    "installable": True,
}
