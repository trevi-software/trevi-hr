# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Employee working hours in contract values",
    "summary": "Set working hours in default contract values.",
    "version": "15.0.1.0.0",
    "category": "Human Resources",
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_contract",
        "hr_contract_values",
        "resource_schedule",
    ],
    "data": [
        "views/hr_contract_init_views.xml",
    ],
    "demo": [
        "data/hr_contract_values_demo.xml",
    ],
    "installable": True,
}
