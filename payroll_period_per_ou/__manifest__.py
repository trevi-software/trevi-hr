# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Period Register per Operating Unit",
    "summary": "Generate separate payroll sheets for each OU.",
    "version": "15.0.1.0.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "payroll_operating_unit",
        "payroll_periods",
    ],
    "data": [
        "views/hr_payroll_period_schedule_view.xml",
        "views/hr_payroll_period_view.xml",
    ],
    "demo": [],
    "installable": True,
}
