# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Employee Infraction Management",
    "version": "14.0.1.0.0",
    "category": "Human Resource",
    "author": "TREVI Software, Michael Telahun Makonnen",
    "license": "AGPL-3",
    "website": "https://github.com/trevi-software/trevi-hr",
    "depends": ["hr", "hr_employee_status", "hr_job_transfer", "group_payroll_manager"],
    "data": [
        "security/hr_security.xml",
        "security/ir_rule.xml",
        "security/ir.model.access.csv",
        "wizard/action.xml",
        "data/hr_infraction_data.xml",
        "views/hr_infraction_view.xml",
        "wizard/batch_view.xml",
    ],
    "installable": True,
}
