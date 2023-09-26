# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "New Employee Wizard",
    "summary": "Streamline the creation of a new employee record",
    "version": "15.0.1.0.0",
    "category": "Human Resources",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_benefit",
        # 'ethiopic_calendar',
        "hr_contract_reference",
        "hr_contract_values_payroll",
        "hr_contract_values_resource_schedule",
        "hr_employee_status",
        # 'hr_recruitment_streamline',
        # 'hr_employee_education',
        "hr_recruitment",
        "payroll_period_contract_values",
        "payroll_periods",
        "payroll_policy_group",
        "resource_schedule",
    ],
    "data": [
        "security/ir.model.access.csv",
        # 'data/hr_recruitment_data.xml',
        "wizard/hr_employee_wizard_views.xml",
        "views/hr_recruitment_view.xml",
    ],
    "installable": True,
}
