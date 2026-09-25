# Copyright (C) 2026 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api


def pre_init_hook(env_or_cr):
    """Backfill NULL departments on hr.job.

    This module makes hr.job.department_id required. Odoo's own demo data
    (hr.job_trainee) has no department, which would leave NULL values and
    make PostgreSQL reject the NOT NULL constraint (CI treats that as an
    error). Assign jobs without a department to the company's admin
    department, creating one if necessary.
    """
    if isinstance(env_or_cr, api.Environment):
        cr = env_or_cr.cr
    else:
        cr = env_or_cr

    cr.execute("SELECT id FROM hr_job WHERE department_id IS NULL")
    if not cr.fetchall():
        return

    cr.execute("SELECT id FROM hr_department ORDER BY id LIMIT 1")
    row = cr.fetchone()
    if row:
        dept_id = row[0]
    else:
        env = api.Environment(cr, SUPERUSER_ID, {})
        dept_id = env["hr.department"].create({"name": "Administration"}).id

    cr.execute(
        "UPDATE hr_job SET department_id = %s WHERE department_id IS NULL",
        (dept_id,),
    )
