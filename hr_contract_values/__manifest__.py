# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Contracts - Initial Settings",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "base",
        "hr",
        "hr_contract",
        "trevi_hr_job_categories",
        "trevi_hr_usability",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/hr_contract_view.xml",
    ],
    "demo": [
        "data/hr_contract_values_demo.xml",
    ],
    "installable": True,
}
