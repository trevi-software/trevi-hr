# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Time Bank",
    "summary": "Basic framework for recording accruals to a time bank",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_holidays",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/accrual_data.xml",
        "views/hr_accrual_view.xml",
    ],
    "installable": True,
}
