# Copyright (C) 2023 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

# pylint: disable=pointless-statement
{
    "name": "Leave Type Unique - Preinstall",
    "summary": "Technical module depended on by Leave Type Unique",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_holidays",
    ],
    "data": [
        "data/hr_holidays_data.xml",
    ],
    "installable": True,
}
