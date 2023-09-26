# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Employment Status",
    "summary": "Track the HR status of employees",
    "version": "15.0.1.0.0",
    "category": "Human Resources",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_contract_status",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "wizard/end_contract_view.xml",
        "data/hr_employee_data.xml",
        "views/hr_view.xml",
    ],
    "installable": True,
}
