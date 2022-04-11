# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class HrApplicant(models.Model):

    _name = "hr.applicant"
    _inherit = "hr.applicant"

    gender = fields.Selection(selection=[("f", "Female"), ("m", "Male")])
    birth_date = fields.Date()
    education = fields.Selection(
        selection=[
            ("none", "No Formal Education"),
            ("primary", "Primary School"),
            ("secondary", "Secondary School"),
            ("diploma", "Diploma"),
            ("degree1", "First Degree"),
            ("masters", "Masters Degree"),
            ("phd", "PhD"),
        ]
    )

    def create_employee_from_applicant(self):

        res = super(HrApplicant, self).create_employee_from_applicant()

        for applicant in self:
            vals = {
                "gender": applicant.gender == "f" and "female" or "male",
                "birthday": applicant.birth_date,
                "education": applicant.education,
            }
            applicant.emp_id.write(vals)

        return res
