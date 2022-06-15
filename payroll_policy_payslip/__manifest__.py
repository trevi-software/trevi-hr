# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payroll Policy Payslip",
    "summary": "Apply payroll policies duing payslip processing",
    "version": "14.0.1.0.0",
    "category": "Payroll",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_accrual_bank",
        "hr_attendance",
        "hr_attendance_day",
        "hr_holidays_public",
        "payroll",
        "payroll_policy_absence",
        "payroll_policy_accrual",
        "payroll_policy_group",
        "payroll_policy_ot",
        "payroll_policy_presence",
    ],
    "data": [
        "security/payroll_policy_payslip_security.xml",
    ],
    "installable": True,
}
