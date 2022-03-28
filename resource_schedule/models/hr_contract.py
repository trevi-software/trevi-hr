# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import api, fields, models


class HrContract(models.Model):

    _inherit = "hr.contract"

    default_area_id = fields.Many2one("resource.schedule.area", "Default shift area")

    @api.onchange("resource_calendar_id")
    def _onchange_resource_calendar_id(self):
        for c in self:
            c.employee_id.resource_id.calendar_id = c.resource_calendar_id

    def create(self, vals):

        res = super(HrContract, self).create(vals)

        # Update resource.calendar on employee resource record
        if "resource_calendar_id" in vals:
            resource_ids = res.mapped("employee_id").mapped("resource_id")
            resource_ids.update({"calendar_id": vals["resource_calendar_id"]})

        ee = res.employee_id
        dToday = fields.Date.today()
        dStart = res.date_start

        # Only create schedule when the employee is first hired. Do not
        # create a schedule if the contract is in the past.
        if len(ee.contract_ids) != 1 or (res.date_end and res.date_end < dToday):
            return res

        # Get End date by trying to figure out when the next mass schedule will be created
        #
        dEnd = None
        xref = self.env.ref("resource_schedule.mass_schedule_cron")
        if xref:
            dEnd = fields.Datetime.from_string(xref.nextcall).date()

        if dEnd is None or dEnd < dStart:
            dEnd = dStart
        while dEnd.weekday() != 6:
            dEnd += timedelta(days=+1)

        # The contract start date may be way back in the past, so use today's date
        # as the start date if the contract started before today.
        if dStart < dToday:
            dStart = dToday
        # Go back to Monday of this week
        while dStart.weekday() != 0:
            dStart += timedelta(days=-1)

        sched_obj = self.env["resource.schedule.shift"]
        dTmp = dStart
        while dTmp < dEnd:
            calendar = res.resource_calendar_id

            # Only create the schedule if there isn't one already.
            #
            prev_sched_ids = sched_obj.search(
                [
                    ("resource_id", "=", ee.resource_id.id),
                    ("day", "=", dTmp),
                ]
            )
            if len(prev_sched_ids) == 0:
                sched_obj.sudo().create_schedule(
                    ee.resource_id, dTmp, dTmp + timedelta(days=6), calendar
                )

            dTmp += timedelta(days=7)

        return res

    def write(self, values):

        res = super().write(values)

        # Update resource.calendar on employee resource record
        if "resource_calendar_id" in values:
            resource_ids = self.mapped("employee_id").mapped("resource_id")
            resource_ids.update({"calendar_id": values["resource_calendar_id"]})

        return res
