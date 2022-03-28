# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResCompany(models.Model):

    _inherit = "res.company"

    @api.model
    def _update_data_resource_calendar(self):
        self.search([("resource_calendar_id", "!=", False)])._create_resource_calendar()

    def _create_resource_calendar(self):

        super()._create_resource_calendar()

        for company in self:
            for att in company.resource_calendar_id.attendance_ids:
                morning = self.env.ref("resource_schedule.attendance_template_0")
                afternoon = self.env.ref("resource_schedule.attendance_template_1")
                if not att.template_id and att.hour_from == 8 and att.hour_to == 12:
                    att.template_id = morning
                elif not att.template_id and att.hour_from == 13 and att.hour_to == 17:
                    att.template_id = afternoon
