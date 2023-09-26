# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payroll Absence Policy",
    "summary": "Define properties of an employee absense policy for payroll.",
    "version": "15.0.1.0.0",
    "category": "Payroll",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_holidays",
        "payroll_policy_group",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_policy_absence_view.xml",
    ],
    "installable": True,
}
