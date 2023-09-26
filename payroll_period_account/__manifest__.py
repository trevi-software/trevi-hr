# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Period Account",
    "summary": "Links payroll periods to accounting",
    "version": "15.0.1.0.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "payroll_account",
        "payroll_periods",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
