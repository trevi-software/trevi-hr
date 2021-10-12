# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo import fields, models


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    benefit_policy_ids = fields.One2many(
        string="Benefits", comodel_name="hr.benefit.policy", inverse_name="employee_id"
    )
    benefit_policies_count = fields.Integer(
        string="Policies", compute="_compute_policies_count"
    )
    benefit_claims_count = fields.Integer(
        string="Claims", compute="_compute_claims_count"
    )

    def _compute_policies_count(self):
        HrBenefitPolicy = self.env["hr.benefit.policy"]
        dToday = date.today()
        for ee in self:
            ee.benefit_policies_count = HrBenefitPolicy.search_count(
                [
                    ("id", "in", ee.benefit_policy_id.ids),
                    ("employee_id", "=", ee.id),
                    ("start_date", "<=", dToday),
                    ("state", "!=", "done"),
                    "|",
                    ("end_date", "=", False),
                    ("end_date", ">=", dToday),
                ]
            )

    def _compute_claims_count(self):
        Claim = self.env["hr.benefit.claim"]
        for ee in self:
            ee.benefit_claims_count = Claim.search_count(
                [
                    ("employee_id", "=", ee.id),
                    ("state", "!=", "decline"),
                ]
            )
