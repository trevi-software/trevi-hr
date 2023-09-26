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

    @api.model_create_multi
    def create(self, lst):

        res = super().create(lst)
        for r in res:
            if r and r.resource_calendar_id:
                resources = r.mapped("employee_id").mapped("resource_id")
                resources.write({"calendar_id": r.resource_calendar_id.id})

        return res
