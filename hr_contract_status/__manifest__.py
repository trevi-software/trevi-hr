# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Employee Contract Status",
    "summary": "Notifications on employee contracts about to end.",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_contract_values",
        "trevi_hr_usability",
    ],
    "pre_init_hook": "pre_init_hook",
    "data": [
        "security/ir.model.access.csv",
        "data/hr_version_data.xml",
        "views/hr_version_view.xml",
        "views/res_config_view.xml",
    ],
}
