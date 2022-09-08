# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "DO NOT USE - Payroll Operating Unit",
    "summary": "WARNING-this module will be removed.",
    "version": "14.0.1.1.0",
    "category": "Payroll",
    "images": ["static/src/img/main_screenshot.png"],
    "author": "TREVI Software, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_contract_operating_unit",
        "hr_operating_unit",
        "operating_unit",
        "payroll",
        # XXX - This is to prevent Odoo's App store bot from picking this up
        "hr_holidays_public",
    ],
    "data": [
        "security/hr_payslip_security.xml",
        "views/hr_payslip_view.xml",
    ],
    "installable": True,
}
