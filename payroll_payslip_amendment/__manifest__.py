# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Pay Slip Amendment",
    "summary": "Add amendments to current and future pay slips",
    "version": "15.0.1.0.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "payroll",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_payslip_amendment_view.xml",
    ],
    "installable": True,
}
