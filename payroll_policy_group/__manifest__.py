# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payroll Policy Groups",
    "summary": "Group payroll policies and assign them to contracts",
    "version": "14.0.1.0.1",
    "category": "Payroll",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "images": ["static/src/img/main_screenshot.png"],
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr_contract",
        "hr_contract_values_payroll",
        "payroll",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_policy_group_view.xml",
    ],
    "demo": [
        "data/hr_payroll_policy_demo.xml",
    ],
    "installable": True,
}
