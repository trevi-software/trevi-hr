# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Overtime Policy",
    "summary": "Assign over-time policies to a policy group",
    "version": "15.0.1.0.0",
    "category": "Generic Modules/Human Resources",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "payroll_policy_accrual",
        "payroll_policy_group",
        "payroll",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_policy_ot_view.xml",
    ],
    "installable": True,
}
