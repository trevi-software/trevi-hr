# Copyright (C) 2022 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from pytz import common_timezones

from odoo import _, api, fields, models


class HrPolicy(models.Model):

    _name = "hr.policy.rounding"
    _order = "date desc"
    _description = "Attendance Rounding Policy"

    @api.model
    def _tz_list(self):

        res = tuple()
        for name in common_timezones:
            res += ((name, name),)
        return res

    name = fields.Char(required=True)
    date = fields.Date(string="Effective Date", required=True)
    tz = fields.Selection(selection=_tz_list, string="Time Zone", required=True)
    line_ids = fields.One2many(
        string="Policy Lines",
        comodel_name="hr.policy.line.rounding",
        inverse_name="policy_id",
    )

    # Return records with latest date first
    @api.model
    def get_latest_policy(self, policy_group, dToday):
        """Return a rounding policy with an effective date on or before dToday but
        greater than all the others"""

        if not policy_group or not policy_group.rounding_policy_ids or not dToday:
            return None

        res = None
        for policy in policy_group.rounding_policy_ids:
            if policy.date <= dToday:
                if res is None:
                    res = policy
                elif policy.date > res.date:
                    res = policy
        return res

    def process_rounding_policy(self, utcdt, action, shift_record):

        self.ensure_one()

        # 1. Check if it's within the grace period
        #
        res = self.line_ids.check_grace_period(utcdt, action, shift_record)
        if res is not False:
            return res

        # 2. Check if OT has to be pre-authorized
        #
        res = self.line_ids.check_pre_authorized_ot(utcdt, action, shift_record)
        if res is not False:
            return res

        # 3. Do any rounding specified
        #
        res = self.line_ids.do_rounding(utcdt, action, shift_record)

        return res


class PolicyLine(models.Model):

    _name = "hr.policy.line.rounding"
    _description = "Attendance Rounding Policy Line"
    _rec_name = "attendance_type"
    _sql_constraints = [
        (
            "uniq_id_att_type",
            "UNIQUE(id,attendance_type)",
            _("Attendance types must be unique per rounding policy line"),
        )
    ]

    policy_id = fields.Many2one(comodel_name="hr.policy.rounding", string="Policy")
    attendance_type = fields.Selection(
        selection=[("in", "Sign-in"), ("out", "Sign-out")], required=True
    )
    grace = fields.Integer(string="Grace Period")
    round_interval = fields.Integer()
    round_type = fields.Selection(
        selection=[("up", "Up"), ("down", "Down"), ("avg", "Average")], required=True
    )
    preauth_ot = fields.Boolean(string="Pre-authorized OT")

    def check_grace_period(self, utcdt, action, shift_record):

        for line in self:

            # Check if this is an entry type that applies to this line
            #
            if (line.attendance_type == "in") and (action != "sign_in"):
                continue
            elif (line.attendance_type == "out") and (action != "sign_out"):
                continue

            utcdtIn, utcdtOut, _shift = shift_record
            if line.attendance_type == "in":
                if (utcdtIn < utcdt) and utcdt <= (
                    utcdtIn + timedelta(minutes=+(line.grace))
                ):
                    return fields.Datetime.to_string(utcdtIn)
            if line.attendance_type == "out":
                if (
                    utcdtOut - timedelta(minutes=line.grace)
                ) <= utcdt and utcdt < utcdtOut:
                    return fields.Datetime.to_string(utcdtOut)
        return False

    def check_pre_authorized_ot(self, utcdt, action, shift_record):

        for line in self:

            # Check if this is an entry type that applies to this line
            #
            if (line.attendance_type == "in") and (action != "sign_in"):
                continue
            elif (line.attendance_type == "out") and (action != "sign_out"):
                continue

            if line.preauth_ot:
                utcdtIn, utcdtOut, _shift = shift_record
                if line.attendance_type == "in" and action == "sign_in":
                    if utcdt < utcdtIn:
                        return utcdtIn

                if line.attendance_type == "out" and action == "sign_out":
                    if utcdt > utcdtOut:
                        return utcdtOut
        return False

    def calculate_rounding_clock_in(self, utcdt, shift_record):

        self.ensure_one()
        new_time = False
        utcdtBottom = utcdt
        utcdtTop = utcdt
        utcdtIn, utcdtOut, _shift = shift_record

        # Sign-in: punch time is less than scheduled time
        if utcdt <= utcdtIn:
            if self.round_type in ["down", "avg"]:
                utcdtBottom = utcdtIn
                while utcdtBottom > utcdt:
                    utcdtBottom -= timedelta(minutes=self.round_interval)
            if self.round_type in ["up", "avg"]:
                utcdtPrevTop = utcdtIn
                utcdtTop = utcdtIn
                while utcdtTop >= utcdt:
                    utcdtPrevTop = utcdtTop
                    utcdtTop += timedelta(minutes=-(self.round_interval))
                utcdtTop = utcdtPrevTop

        # Sign-in: punch time is greater than scheduled time
        if (utcdt > utcdtIn) and (utcdt < utcdtOut):
            if self.round_type in ["down", "avg"]:
                utcdtPrevBottom = utcdtIn
                utcdtBottom = utcdtIn
                while utcdtBottom <= utcdt:
                    utcdtPrevBottom = utcdtBottom
                    utcdtBottom += timedelta(minutes=+(self.round_interval))
                utcdtBottom = utcdtPrevBottom
            if self.round_type in ["up", "avg"]:
                utcdtTop = utcdtIn
                while utcdtTop < utcdt:
                    utcdtTop += timedelta(minutes=+(self.round_interval))

        # Calculate the new rounded time
        if self.round_type == "down":
            new_time = fields.Datetime.to_string(utcdtBottom)
        elif self.round_type == "up":
            new_time = fields.Datetime.to_string(utcdtTop)
        elif self.round_type == "avg":
            delta = (utcdtTop - utcdtBottom).total_seconds()
            utcdtMiddle = utcdtBottom + timedelta(seconds=(delta / 2))
            new_time = (
                (utcdt < utcdtMiddle)
                and fields.Datetime.to_string(utcdtBottom)
                or fields.Datetime.to_string(utcdtTop)
            )

        return new_time

    def calculate_rounding_clock_out(self, utcdt, shift_record):

        self.ensure_one()
        new_time = False
        utcdtBottom = utcdt
        utcdtTop = utcdt
        utcdtIn, utcdtOut, _shift = shift_record

        # Sign-out: punch time is less than scheduled time
        if utcdt <= utcdtOut:
            if self.round_type in ["down", "avg"] and not self.preauth_ot:
                utcdtBottom = utcdtOut
                while utcdtBottom > utcdt:
                    utcdtBottom += timedelta(minutes=-(self.round_interval))
            if self.round_type in ["up", "avg"]:
                utcdtPrevTop = utcdtOut
                utcdtTop = utcdtOut
                while utcdtTop >= utcdt:
                    utcdtPrevTop = utcdtTop
                    utcdtTop += timedelta(minutes=-(self.round_interval))
                utcdtTop = utcdtPrevTop

        # Sign-out: punch time is greater than scheduled time
        if utcdt > utcdtOut:

            if self.round_type in ["down", "avg"]:
                utcdtPrevBottom = utcdtIn
                utcdtBottom = utcdtIn
                while utcdtBottom <= utcdt:
                    utcdtPrevBottom = utcdtBottom
                    utcdtBottom += timedelta(minutes=+(self.round_interval))
                utcdtBottom = utcdtPrevBottom
            if self.round_type in ["up", "avg"]:
                utcdtTop = utcdtIn
                while utcdtTop < utcdt:
                    utcdtTop += timedelta(minutes=+(self.round_interval))

        # Calculate the new rounded time
        if self.round_type == "down":
            new_time = fields.Datetime.to_string(utcdtBottom)
        elif self.round_type == "up":
            new_time = fields.Datetime.to_string(utcdtTop)
        elif self.round_type == "avg":
            delta = (utcdtTop - utcdtBottom).total_seconds()
            utcdtMiddle = utcdtBottom + timedelta(seconds=(delta / 2))
            new_time = (
                (utcdt < utcdtMiddle)
                and fields.Datetime.to_string(utcdtBottom)
                or fields.Datetime.to_string(utcdtTop)
            )

        return new_time

    def do_rounding(self, utcdt, action, shift_record):

        new_time = False
        for line in self:

            # Check if this is an entry type that applies to this line
            #
            if (line.attendance_type == "in") and (action != "sign_in"):
                continue
            elif (line.attendance_type == "out") and (action != "sign_out"):
                continue

            if line.round_interval > 0:

                if line.attendance_type == "in" and action == "sign_in":
                    return line.calculate_rounding_clock_in(utcdt, shift_record)

                if line.attendance_type == "out" and action == "sign_out":
                    return line.calculate_rounding_clock_out(utcdt, shift_record)

        return new_time
