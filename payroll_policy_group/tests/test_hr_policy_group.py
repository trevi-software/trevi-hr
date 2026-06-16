# Copyright (C) 2021 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common


class TestAccrualPolicy(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.PolicyGroup = cls.env["hr.policy.group"]
        cls.Policy = cls.env["hr.policy.accrual"]
        cls.PolicyLine = cls.env["hr.policy.line.accrual"]
        cls.AccrualJob = cls.env["hr.policy.line.accrual.job"]
        cls.Accrual = cls.env["hr.accrual"]
        cls.Employee = cls.env["hr.employee"]
        cls.LeaveType = cls.env["hr.leave.type"]
        cls.LeaveAlloction = cls.env["hr.leave.allocation"]
