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
    def get_latest_policy(self, policy_group, today=None):
        """
        Return an accrual policy with an effective date before today but
        greater than all the others
        """

        if not policy_group or not policy_group.accr_policy_ids or not today:
            return None

        accrual_policy = None
        for policy in policy_group.accr_policy_ids:
            policy_date = fields.Date.from_string(policy.date)
            if policy_date <= today:
                if accrual_policy is None or policy_date > fields.Date.from_string(accrual_policy.date):
                    accrual_policy = policy

        return accrual_policy

    @api.model
    def try_calculate_accruals(self):

        policy_group = self.env["hr.policy.group"]
        accrual_job = self.env["hr.policy.line.accrual.job"]

        today = fields.Date.from_string(fields.Date.today())

        for pg in policy_group.search([]):
            accrual_policy = self.get_latest_policy(pg, today)
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
                    line_jobs[line.id] = [today]
                else:
                    line_jobs[line.id] = []
                    while d < today:
                        d += timedelta(days=1)
                        line_jobs[line.id].append(d)

            # For each accrual line in this accrual policy do a run for each day (beginning
            # from the last date for which it was run) until today for each contract attached
            # to the policy group.
            #
            for line in accrual_policy.line_ids:
                if line.type not in ["calendar"]:
                    continue

                for job_date in line_jobs[line.id]:

                    # Create a Job for the accrual line
                    job_vals = {
                        "name": job_date,
                        "execution_time": fields.Datetime.now(),
                        "policy_line_id": line.id,
                    }
                    job = accrual_job.create(job_vals)

                    employee_list = []
                    for contract in pg.contract_ids:
                        # employee already done or contract not in running state
                        if (
                            contract.employee_id.id in employee_list
                            or contract.state in ["draft", "done"]
                        ):
                            continue
                        # contract has already ended
                        if contract.date_end and contract.date_end < job_date:
                            continue
                        line.calculate_and_deposit(
                            contract.employee_id, job, dToday=job_date
                        )

                        # An employee may have multiple valid contracts. Don't double-count.
                        employee_list.append(contract.employee_id.id)
                    job.end_time = datetime.now()

    @api.model
    def do_accrual_by_period(self, policy_line, employee, start_date, end_date, descr=None):

        res = True
        if not start_date or not end_date or policy_line.type not in ["calendar"]:
            return False

        today = start_date
        while today <= end_date:
            policy_line.calculate_and_deposit(
                employee, job_id=False, dToday=today, descr=descr
            )
            today += timedelta(days=+1)

        return res
