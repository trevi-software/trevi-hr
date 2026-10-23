# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import api, fields, models


class HrVersion(models.Model):
    _inherit = "hr.version"

    default_area_id = fields.Many2one("resource.schedule.area", "Default shift area")

    @api.onchange("resource_calendar_id")
    def _onchange_resource_calendar_id(self):
        for c in self:
            c.employee_id.resource_id.calendar_id = c.resource_calendar_id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for res, vals in zip(records, vals_list, strict=True):
            # Update resource.calendar on employee resource record
            if "resource_calendar_id" in vals:
                resource_ids = res.mapped("employee_id").mapped("resource_id")
                resource_ids.update({"calendar_id": vals["resource_calendar_id"]})

            ee = res.employee_id
            dToday = fields.Date.today()
            dStart = res.date_start

            # Only create a schedule when an employee is first hired. In Odoo 19
            # every employee record already has an hr.version, so the "first
            # contract" is the first version carrying a contract start date.
            contract_versions = ee.version_ids.filtered("contract_date_start")
            if not dStart or res not in contract_versions:
                continue
            if len(contract_versions) != 1:
                continue
            # Do not create a schedule if the contract is in the past.
            if res.date_end and res.date_end < dToday:
                continue

            # Get End date by trying to figure out when the next mass schedule will
            # be created.
            #
            dEnd = None
            xref = self.env.ref("resource_schedule.mass_schedule_cron")
            if xref:
                dEnd = fields.Datetime.to_datetime(xref.nextcall).date()

            if dEnd is None or dEnd < dStart:
                dEnd = dStart
            while dEnd.weekday() != 6:
                dEnd += timedelta(days=+1)

            # The contract start date may be way back in the past, so use today's date
            # as the start date if the contract started before today.
            dStart = max(dStart, dToday)
            # Go back to Monday of this week
            while dStart.weekday() != 0:
                dStart += timedelta(days=-1)

            sched_obj = self.env["resource.schedule.shift"]
            calendar = res.resource_calendar_id
            _, start_week = sched_obj._get_calendar_and_start_week(
                ee.resource_id, calendar
            )
            max_week = 0
            if calendar.attendance_ids:
                max_week = calendar.attendance_ids.sorted("sequence")[-1].week_nbr

            # Compute the days off for the whole range once so a rolling day
            # off rotation is carried consistently across the weekly calls,
            # and then walk the weeks week by week, skipping the ones that are
            # already scheduled. This keeps both the rotation week and the
            # rolling days off in step.
            all_daysoff = sched_obj.get_daysoff(ee.resource_id, calendar, dStart, dEnd)
            dTmp = dStart
            week_nbr = 0
            week = start_week
            while dTmp < dEnd:
                prev_sched_ids = sched_obj.search(
                    [
                        ("resource_id", "=", ee.resource_id.id),
                        ("day", "=", dTmp),
                    ]
                )
                if not prev_sched_ids:
                    if week_nbr < len(all_daysoff):
                        week_daysoff = all_daysoff[week_nbr]
                    else:
                        week_daysoff = all_daysoff[-1] if all_daysoff else []
                    sched_obj.sudo().create_schedule(
                        ee.resource_id,
                        dTmp,
                        dTmp + timedelta(days=6),
                        calendar,
                        start_week=week,
                        daysoff=[week_daysoff],
                    )

                dTmp += timedelta(days=7)
                week_nbr += 1
                if max_week:
                    week = 0 if week >= max_week else week + 1

        return records

    def write(self, values):
        res = super().write(values)

        # Update resource.calendar on employee resource record
        if "resource_calendar_id" in values:
            resource_ids = self.mapped("employee_id").mapped("resource_id")
            resource_ids.update({"calendar_id": values["resource_calendar_id"]})

        return res
