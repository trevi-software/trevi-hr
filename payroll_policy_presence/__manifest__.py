# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payroll Presence Policy",
    "summary": "Define properties of an employee presence policy",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_accrual_bank",
        "payroll",
        "payroll_policy_accrual",
        "payroll_policy_group",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_policy_presence_view.xml",
    ],
    "installable": True,
}
