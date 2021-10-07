# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Currency Denominations",
    "category": "Finance",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "images": ["static/src/img/main_screenshot.png"],
    "version": "14.0.1.0.0",
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/res_currency_denomination.xml",
        "views/res_currency_view.xml",
    ],
    "installable": True,
}
