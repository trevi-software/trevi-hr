# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ResourceScheduleGenerate(models.TransientModel):

    _name = "resource.schedule.generate"
    _description = "Generate Schedules Wizard"

    date_start = fields.Date(string="Start", required=True)
    no_weeks = fields.Integer(string="Number of weeks", default=2, required=True)
    type = fields.Selection(
        selection=[
            ("employee", "Employee"),
            ("team", "Team"),
            (
                "calendar",
                "Working Schedule",
            ),
        ],
        required=True,
        default="employee",
        help="Choose how to schedule shifts."
        "Employee - Directly choose the employees for which to schedule shifts."
        "Team - Shifts will be scheduled for all the employees in the team(s)."
        "Working Schedule - All employees (and teams) that have been assigned that"
        "schedule will have shifts scheduled.",
    )
    employee_ids = fields.Many2many(
        string="Employees",
        comodel_name="hr.employee",
        relation="hr_employee_schedule_rel",
        column1="generate_id",
        column2="employee_id",
    )
    resource_calendar_id = fields.Many2one("resource.calendar", "Working Schedule")
    schedule_team_ids = fields.Many2many("resource.schedule.team", string="Teams")

    @api.onchange("date_start")
    def onchange_date_start(self):

        for rec in self:
            # The schedule must start on a Monday
            if rec.date_start and rec.date_start.weekday() != 0:
                dStart = rec.date_start
                while dStart.weekday() != 0:
                    dStart -= timedelta(days=1)
                rec.date_start = dStart

    @api.onchange("resource_calendar_id")
    def _onchange_resource_calendar_id(self):

        for rec in self:
            if rec.type == "calendar" and rec.resource_calendar_id:
                resources = self.env["resource.resource"].search(
                    [("calendar_id", "=", rec.resource_calendar_id.id)]
                )
                employees = self.env["hr.employee"].search(
                    [("resource_id", "in", resources.ids)]
                )
                rec.employee_ids = [(6, 0, employees.ids)]
            elif not rec.resource_calendar_id:
                rec.employee_ids = [(4, 0, 0)]

    def generate_schedules(self):

        Schedule = self.env["resource.schedule.shift"]
        dStart = self.date_start
        dEnd = dStart + relativedelta(weeks=abs(self.no_weeks), days=-1)

        shifts = self.env["resource.schedule.shift"]
        for ee in self.employee_ids:

            # If there are overlapping schedules, don't create
            #
            dTmp = dStart
            overlap_sched_ids = Schedule.search(
                [
                    ("resource_id", "=", ee.resource_id.id),
                    ("day", "<=", dEnd),
                    ("day", ">=", dTmp),
                ]
            )
            if len(overlap_sched_ids) > 0:
                if overlap_sched_ids[-1].day < dEnd:
                    dTmp = overlap_sched_ids[-1].day + timedelta(days=1)

            shifts |= ee.create_schedule(dTmp, dEnd)

        return {
            "view_mode": "timeline,calendar,tree,form",
            "res_model": "resource.schedule.shift",
            "domain": [("id", "in", shifts.ids)],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": self.env.context,
        }
