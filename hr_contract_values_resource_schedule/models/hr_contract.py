# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrContract(models.Model):

    _inherit = "hr.contract"

    @api.model
    def _get_resource_calendar(self):

        res = self.env.company.resource_calendar_id.id
        init = self.get_latest_initial_values()
        if init is not None and init.resource_calendar_id:
            res = init.resource_calendar_id.id
        return res

    resource_calendar_id = fields.Many2one(default=_get_resource_calendar)

    def create(self, values):

        res = super().create(values)
        if res and res.resource_calendar_id:
            resources = res.mapped("employee_id").mapped("resource_id")
            resources.write({"calendar_id": res.resource_calendar_id.id})

        return res
