# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Manager",
    "summary": "Permissions group Payroll Manager",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "ir_module_category_payroll",
        "hr",
        "hr_contract",
    ],
    "data": [
        "security/hr_security.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
    ],
    "installable": True,
}
