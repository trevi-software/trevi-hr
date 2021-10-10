# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrJobStateWizard(models.TransientModel):

    _name = "hr.job.wizard.state.change"
    _description = "Change recruitment state of jobs in batches"

    @api.model
    def _get_jobs(self):

        res = []
        if self.env.context.get("active_ids", False):
            res = self.env.context["active_ids"]

        return res

    job_ids = fields.Many2many(
        comodel_name="hr.job",
        relation="hr_job_state_change_wizard_rel",
        column1="wizard_id",
        column2="job_id",
        default=_get_jobs,
        string="Jobs",
    )
    do_open = fields.Boolean(string="Close Recruitment")
    do_recruit = fields.Boolean(string="Open for Recruitment")

    @api.onchange("do_open")
    def _onchange_open(self):
        if self.do_open:
            self.do_recruit = False

    @api.onchange("do_recruit")
    def _onchange_recruit(self):
        if self.do_recruit:
            self.do_open = False

    def change_state(self):

        if self.do_open:
            self.job_ids.set_open()
        elif self.do_recruit:
            self.job_ids.set_recruit()

        return {"type": "ir.actions.act_window_close"}
