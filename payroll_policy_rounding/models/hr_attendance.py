# Copyright (C) 2022 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class HrAttendance(models.Model):

    _inherit = "hr.attendance"

    clock_in = fields.Datetime()
    clock_out = fields.Datetime()

    @api.model
    def _get_schedule(self, ee_id, d, contract):

        sched_hours = []
        if contract:
            ResourceShift = self.env["resource.schedule.shift"]
            shifts = ResourceShift.search(
                [
                    ("employee_id", "=", ee_id),
                    ("day", "=", d),
                ]
            )
            sched_hours = shifts.datetimes_naive_utc()
        return sched_hours

    @api.model
    def _get_schedule_by_approximation(self, ee_id, action, utcdt, contract):

        shift_records = self._get_schedule(ee_id, utcdt.date(), contract)
        dtBestIn = dtBestOut = shiftBest = previousDelta = False
        for utcIn, utcOut, shift in shift_records:
            if action == "sign_in":
                delta = abs((utcdt - utcIn).total_seconds())
                if utcIn == utcdt:
                    return (utcIn, utcOut, shift)
                elif delta <= (8 * 60 * 60):
                    if previousDelta is False or (delta < previousDelta):
                        previousDelta = delta
                        dtBestIn = utcIn
                        dtBestOut = utcOut
                        shiftBest = shift
            elif action == "sign_out":
                delta = abs((utcdt - utcOut).total_seconds())
                if utcOut == utcdt:
                    return (utcIn, utcOut, shift)
                elif delta <= (8 * 60 * 60):
                    if previousDelta is False or (delta < previousDelta):
                        previousDelta = delta
                        dtBestIn = utcIn
                        dtBestOut = utcOut
                        shiftBest = shift
        return (dtBestIn, dtBestOut, shiftBest)

    @api.model
    def get_contract_by_date(self, ee_id, d):

        con_ids = self.env["hr.contract"].search(
            [
                ("employee_id", "=", ee_id),
                ("date_start", "<=", d),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", d),
            ]
        )

        if len(con_ids) > 0:
            return con_ids[0]
        else:
            return False

    @api.model
    def _process_policy(self, employee_id, vals):

        PolicyRounding = self.env["hr.policy.rounding"]
        res = vals.copy()
        contract = False
        if res.get("clock_in", False) and not res.get("check_in", False):
            rp = None
            dt = fields.Datetime.from_string(res["clock_in"])
            res.update({"check_in": res["clock_in"]})
            contract = self.get_contract_by_date(employee_id, dt.date())
            if contract:
                rp = PolicyRounding.get_latest_policy(
                    contract.policy_group_id, dt.date()
                )
            if rp is not None:
                shift_record = tuple(
                    self._get_schedule_by_approximation(
                        employee_id, "sign_in", dt, contract
                    )
                )
                if shift_record and shift_record[2]:
                    res.update({"schedule_shift_id": shift_record[2].id})
                    new_time = rp.process_rounding_policy(dt, "sign_in", shift_record)
                    if new_time:
                        res.update({"check_in": new_time})

        if res.get("clock_out", False) and not res.get("check_out", False):
            rp = None
            dt = fields.Datetime.from_string(res["clock_out"])
            res.update({"check_out": res["clock_out"]})
            contract = self.get_contract_by_date(employee_id, dt.date())
            if contract:
                rp = PolicyRounding.get_latest_policy(
                    contract.policy_group_id, dt.date()
                )
            if rp is not None:
                shift_record = self._get_schedule_by_approximation(
                    employee_id, "sign_out", dt, contract
                )
                if shift_record and shift_record[2]:
                    res.update({"schedule_shift_id": shift_record[2].id})
                    new_time = rp.process_rounding_policy(dt, "sign_out", shift_record)
                    if new_time:
                        res.update({"check_out": new_time})

        return res

    @api.model
    def create(self, vals):

        vals = self._process_policy(vals["employee_id"], vals)

        return super(HrAttendance, self).create(vals)

    def write(self, vals):

        for rec in self:
            vals = self._process_policy(rec.employee_id.id, vals)
            res = super().write(vals)

        return res
