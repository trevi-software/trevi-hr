# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Register",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "website": "https://github.com/trevi-software/trevi-hr",
    "images": ["static/src/img/main_screenshot.png"],
    "depends": [
        "currency_denomination",
        "payroll",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/hr_payroll_register_run_view.xml",
        # 'report/hr_payroll_register_report.xml',
        "views/hr_payroll_register_view.xml",
    ],
    "installable": True,
}
