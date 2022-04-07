# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Benefit Management",
    "summary": "Assign benefits and deductables to employees",
    "version": "14.0.1.0.1",
    "category": "Human Resources",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_contract_status",
        "hr_employee_seniority_months",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "wizard/end_policy.xml",
        "wizard/enroll_employee_view.xml",
        "wizard/enroll_multi_employee_view.xml",
        "views/benefit_view.xml",
        "views/benefit_premium_view.xml",
        "views/benefit_earning_view.xml",
        "views/benefit_policy_view.xml",
        "views/benefit_claim_view.xml",
        "views/hr_employee_view.xml",
        "data/benefit_sequence.xml",
    ],
    "installable": True,
}
