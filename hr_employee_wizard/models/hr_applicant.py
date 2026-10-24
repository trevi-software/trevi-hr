# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class HrApplicant(models.Model):
    _name = "hr.applicant"
    _inherit = "hr.applicant"

    gender = fields.Selection(selection=[("f", "Female"), ("m", "Male")])
    birth_date = fields.Date()
    id_no = fields.Char(string="Official ID")
    education = fields.Selection(
        selection=[
            ("graduate", "Graduate"),
            ("diploma", "Diploma"),
            ("bachelor", "Bachelor"),
            ("master", "Master"),
            ("doctor", "Doctor"),
            ("other", "Other"),
        ],
    )

    def create_employee_from_applicant(self):
        self.ensure_one()
        res = super().create_employee_from_applicant()

        employee = self.env["hr.employee"].browse(res.get("res_id"))
        if employee:
            vals = {}
            if self.gender:
                vals["sex"] = {"f": "female", "m": "male"}[self.gender]
            if self.birth_date:
                vals["birthday"] = self.birth_date
            if self.education:
                vals["certificate"] = self.education
            if self.id_no:
                vals["identification_id"] = self.id_no
            if vals:
                employee.write(vals)

        return res
