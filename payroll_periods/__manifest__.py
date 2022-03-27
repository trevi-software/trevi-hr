# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payroll Period",
    "summary": "Configurable payroll schedules.",
    "version": "14.0.1.1.2",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_contract",
        "hr_employee_status",
        "payroll",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "data/hr_payroll_period_data.xml",
        "data/hr_payroll_period_cron.xml",
        "views/hr_contract_view.xml",
        "views/hr_payroll_period_view.xml",
        "views/hr_payroll_period_schedule_view.xml",
        "views/hr_payslip_exception_rule_view.xml",
        "views/hr_payslip_exception_view.xml",
        "views/hr_payslip_view.xml",
    ],
    "installable": True,
}
