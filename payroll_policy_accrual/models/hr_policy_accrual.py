# Copyright (C) 2021 TREVI Software
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import api, fields, models


class HrPolicy(models.Model):

    _name = "hr.policy.accrual"
    _description = "Accrual Policy"
    _order = "date desc"

    name = fields.Char(required=True)
    date = fields.Date(string="Effective Date", required=True)
    line_ids = fields.One2many(
        comodel_name="hr.policy.line.accrual",
        inverse_name="policy_id",
        string="Policy Lines",
    )

    # Return records with latest date first
    @api.model
    def get_latest_policy(self, policy_group, dToday=None):
        """
        Return an accrual policy with an effective date before dToday but
        greater than all the others
        """

        if not policy_group or not policy_group.accr_policy_ids or not dToday:
            return None

        res = None
        for policy in policy_group.accr_policy_ids:
            dPolicy = fields.Date.from_string(policy.date)
            if dPolicy <= dToday:
                if res is None:
                    res = policy
                elif dPolicy > fields.Date.from_string(res.date):
                    res = policy

        return res

    @api.model
    def try_calculate_accruals(self):

        PolicyGroup = self.env["hr.policy.group"]
        AccrualJob = self.env["hr.policy.line.accrual.job"]

        dToday = fields.Date.from_string(fields.Date.today())

        for pg in PolicyGroup.search([]):
            accrual_policy = self.get_latest_policy(pg, dToday)
            if accrual_policy is None:
                continue

            # Get the last time that an accrual job was run for each accrual line in
            # the accrual policy. If there was no 'last time' assume this is the first
            # time the job is being run and start it running from today. Otherwise,
            # we must also run jobs for all the skipped dates.
            #
            line_jobs = {}
            for line in accrual_policy.line_ids:
                d = line.get_last_job_date()
                if d is None:
                    line_jobs[line.id] = [dToday]
                else:
                    line_jobs[line.id] = []
                    while d < dToday:
                        d += timedelta(days=1)
                        line_jobs[line.id].append(d)

            # For each accrual line in this accrual policy do a run for each day (beginning
            # from the last date for which it was run) until today for each contract attached
            # to the policy group.
            #
            for line in accrual_policy.line_ids:
                if line.type not in ["calendar"]:
                    continue

                for dJob in line_jobs[line.id]:

                    # Create a Job for the accrual line
                    job_vals = {
                        "name": dJob,
                        "execution_time": fields.Datetime.now(),
                        "policy_line_id": line.id,
                    }
                    job = AccrualJob.create(job_vals)

                    employee_list = []
                    for contract in pg.contract_ids:
                        # employee already done or contract not in running state
                        if (
                            contract.employee_id.id in employee_list
                            or contract.state in ["draft", "done"]
                        ):
                            continue
                        # contract has already ended
                        if contract.date_end and contract.date_end < dJob:
                            continue
                        line.calculate_and_deposit(
                            contract.employee_id, job, dToday=dJob
                        )

                        # An employee may have multiple valid contracts. Don't double-count.
                        employee_list.append(contract.employee_id.id)
                    job.end_time = datetime.now()

    @api.model
    def do_accrual_by_period(self, policy_line, employee, dStart, dEnd, descr=None):

        res = True
        if not dStart or not dEnd or policy_line.type not in ["calendar"]:
            return False

        dToday = dStart
        while dToday <= dEnd:
            policy_line.calculate_and_deposit(
                employee, job_id=False, dToday=dToday, descr=descr
            )
            dToday += timedelta(days=+1)

        return res
