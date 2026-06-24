# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AutopunchLastrun(models.Model):

    _name = "resource.schedule.autopunch.lastrun"
    _description = "Schedule auto-punch last run-time"
    _order = "name desc"

    name = fields.Datetime()
    record_ids = fields.Many2many("hr.attendance")
    record_count = fields.Integer(compute="_compute_record_count")

    @api.depends("record_ids")
    def _compute_record_count(self):

        for rec in self:
            rec.record_count = len(rec.record_ids)
