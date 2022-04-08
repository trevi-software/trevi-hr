# Copyright (C) 2022 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Rounding Policy",
    "summary": "Define attendance check-in and check-out rounding policies",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "author": "TREVI Software,Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_attendance",
        "hr_contract",
        "payroll_policy_group",
        "resource_schedule",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/payroll_policy_view.xml",
    ],
    "installable": True,
}
