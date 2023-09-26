# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Departmental Transfer",
    "category": "HR",
    "version": "15.0.1.0.0",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "base_setup",
        "hr",
        "hr_contract_status",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/hr_transfer_cron.xml",
        "data/hr_transfer_data.xml",
        "views/hr_transfer_view.xml",
    ],
    "installable": True,
}
