# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Contract Payroll Structure Initial Settings",
    "version": "14.0.1.1.0",
    "category": "Payroll",
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_contract",
        "hr_contract_values",
        "payroll",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_contract_init_view.xml",
    ],
    "demo": [
        "data/hr_contract_values_demo.xml",
    ],
    "installable": True,
}
