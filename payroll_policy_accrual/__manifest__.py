# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Time Accrual Policy",
    "summary": "Automatically or manually accrue to time banks to be withdrawn later",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_accrual_bank",
        "hr_contract_status",
        "hr_employee_seniority_months",
        "payroll_policy_group",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/hr_policy_accrual_cron.xml",
        "views/hr_policy_accrual_view.xml",
    ],
    "installable": True,
}
