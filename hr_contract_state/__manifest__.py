# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stateful Employee Contracts",
    "summary": "Workflows and notifications on employee contracts.",
    "version": "14.0.1.0.1",
    "category": "Human Resources",
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_contract",
        "hr_contract_init",
        "hr_security",
        "hr_simplify",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/hr_contract_data.xml",
        "views/hr_contract_view.xml",
        "views/res_config_view.xml",
    ],
    "installable": True,
}
