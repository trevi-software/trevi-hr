# Copyright (C) 2026 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api
from odoo.api import SUPERUSER_ID


def pre_init_hook(env_or_cr):
    """Backfill NULL departments on hr.job.

    This module makes hr.job.department_id required. Odoo's own demo data
    (hr.job_trainee) has no department, which would leave NULL values and
    make PostgreSQL reject the NOT NULL constraint (CI treats that as an
    error). Assign the jobs without a department to a department of their own
    company, creating one if necessary.

    ``hr.job.department_id`` is ``check_company=True``, so the backfill must
    stay within a single company: assigning every orphan job one shared
    department would pair other companies' jobs (and, through them, their
    contracts) with a foreign department.
    """
    if isinstance(env_or_cr, api.Environment):
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    cr = env.cr

    cr.execute("SELECT DISTINCT company_id FROM hr_job WHERE department_id IS NULL")
    company_ids = [row[0] for row in cr.fetchall()]
    if not company_ids:
        return

    departments = env["hr.department"].with_context(active_test=False)
    for company_id in company_ids:
        department = departments.search(
            [("company_id", "=", company_id)], order="id", limit=1
        )
        if not department:
            department = departments.create(
                {"name": "Administration", "company_id": company_id or False}
            )
        cr.execute(
            "UPDATE hr_job SET department_id = %s"
            " WHERE department_id IS NULL AND company_id IS NOT DISTINCT FROM %s",
            (department.id, company_id),
        )
