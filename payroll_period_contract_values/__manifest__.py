# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Period Schedule in Contracts",
    "summary": "Links payroll period schedules with employee contracts.",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "license": "AGPL-3",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_contract",
        "hr_contract_values_payroll",
        "payroll_periods",
    ],
    "data": [
        "views/hr_contract_init_view.xml",
    ],
    "demo": [
        "data/hr_contract_values_demo.xml",
    ],
    "installable": True,
}
