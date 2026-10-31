# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import AccessError


class HrJob(models.Model):
    _inherit = "hr.job"

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("recruit", "Recruitment in Progress"),
            ("open", "Recruitment Closed"),
        ],
        string="Recruitment Status",
        default="draft",
        copy=False,
    )

    def _set_recruitment_state(self, state):
        if not self.env.user.has_group("hr.group_hr_manager"):
            raise AccessError(_("Only HR managers can change recruitment state."))
        self.check_access("write")
        return self.sudo().write({"state": state})

    def set_open(self):
        return self._set_recruitment_state("open")

    def set_recruit(self):
        return self._set_recruitment_state("recruit")
