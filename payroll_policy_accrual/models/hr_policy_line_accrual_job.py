# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAccrualJob(models.Model):

    _name = "hr.policy.line.accrual.job"
    _description = "Accrual Policy Line Job Run"

    name = fields.Date(string="Date", required=True, readonly=True)
    execution_time = fields.Datetime(required=True, readonly=True)
    end_time = fields.Datetime(readonly=True)
    policy_line_id = fields.Many2one(
        string="Accrual Policy Line",
        comodel_name="hr.policy.line.accrual",
        required=True,
        readonly=True,
    )
    accrual_line_ids = fields.Many2many(
        string="Accrual Lines",
        comodel_name="hr.accrual.line",
        relation="hr_policy_job_accrual_line_rel",
        column1="job_id",
        column2="accrual_line_id",
        readonly=True,
    )
    holiday_ids = fields.Many2many(
        string="Leave Allocation Requests",
        comodel_name="hr.leave.allocation",
        relation="hr_policy_job_holiday_rel",
        column1="job_id",
        column2="holiday_id",
        readonly=True,
    )
