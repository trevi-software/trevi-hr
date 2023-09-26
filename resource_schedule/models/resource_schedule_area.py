# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrScheduleArea(models.Model):
    _name = "resource.schedule.area"
    _description = "Scheduling Area"
    _check_company_auto = True

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    resource_ids = fields.One2many("resource.resource", "default_area_id")
    resource_count = fields.Integer(compute="_compute_resource_count")
    color = fields.Integer(string="Color Index")

    def _compute_resource_count(self):
        for area in self:
            area.resource_count = len(area.resource_ids)
