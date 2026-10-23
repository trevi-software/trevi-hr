# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrScheduleGroup(models.Model):
    _name = "resource.schedule.group"
    _description = "Resource Scheduling Group"
    _check_company_auto = True

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    manager_ids = fields.Many2many("res.users")
    attendance_template_ids = fields.Many2many(
        "resource.calendar.attendance.template",
        "resource_attendance_template_schedule_group_rel",
        string="Work Detail Template",
    )
    template_count = fields.Integer(compute="_compute_template_count")
    active = fields.Boolean(default=True)

    def _compute_template_count(self):
        for rec in self:
            rec.template_count = len(rec.attendance_template_ids)
