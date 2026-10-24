# Copyright (C) 2024 Trevi Software (https://trevi.et)
# Copyright (C) 2024 Michael Telahun Makonnen <telahunmike@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _get_certificate_selection(self):
        """Add the ``diploma`` level to the core certificate selection.

        In Odoo 19 ``certificate`` is a ``Selection`` built by this method
        instead of a static list, so ``selection_add`` cannot be used.
        """
        return super()._get_certificate_selection() + [
            ("diploma", self.env._("Diploma"))
        ]
