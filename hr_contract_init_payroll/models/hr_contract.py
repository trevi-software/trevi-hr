# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    @api.model
    def _get_struct(self):

        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.struct_id:
            res = init.struct_id.id
        return res

    struct_id = fields.Many2one(default=_get_struct)
