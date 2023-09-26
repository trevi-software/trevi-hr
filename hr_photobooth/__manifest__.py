# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Photo Booth",
    "summary": "Capture employee picture with webcam",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "author": "TREVI Software",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_photobooth_view.xml",
        "views/assets.xml",
    ],
    "demo": [],
    "installable": True,
}
