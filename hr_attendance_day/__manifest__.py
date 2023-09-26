# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Attendance Day",
    "summary": "Attach a localized date to an attendace record",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "author": "TREVI Software",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_attendance",
    ],
    "data": [
        "views/hr_attendance_view.xml",
    ],
    "installable": True,
}
