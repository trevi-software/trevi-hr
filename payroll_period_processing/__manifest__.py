# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2015 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Period Processing",
    "summary": "Payroll period processing wizard",
    "version": "14.0.1.2.1",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "author": "TREVI Software, Clear ICT Solutions",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_holidays",
        "hr_holidays_public",
        "payroll",
        "payroll_periods",
        "payroll_register",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "wizard/process_view.xml",
        "views/hr_payroll_view.xml",
    ],
    "installable": True,
}
