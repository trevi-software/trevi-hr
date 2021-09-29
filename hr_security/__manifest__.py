# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HR Permission Groups",
    "summary": "Human Resources permissions groups",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_contract",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
    ],
    "installable": True,
}
