# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Simplify Employee Records.",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "Human Resources",
    "author": "TREVI Software",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": [
        "hr",
        "hr_contract",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/hr_simplify_view.xml",
    ],
    "installable": True,
}
