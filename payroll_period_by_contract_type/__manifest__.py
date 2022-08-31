# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Period Batch by contract type",
    "summary": "Generate separate payslip batches for each contract type.",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_contract_type",
        "payroll_periods",
        "payroll_period_processing",
    ],
    "data": [
        "views/hr_payroll_period_schedule_view.xml",
        "wizard/process_view.xml",
    ],
    "demo": [],
    "installable": True,
}
