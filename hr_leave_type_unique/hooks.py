# Copyright (C) 2026 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api


def pre_init_hook(env_or_cr):
    """Backfill NULL codes on hr.leave.type.

    This module makes hr.leave.type.code required and unique per company.
    Existing rows (e.g. Odoo's own demo/data leave types) have no code,
    which would leave NULL values and make PostgreSQL reject the NOT NULL
    constraint (CI treats the resulting schema error as a failure). Derive
    a deterministic unique code per company from the record id.
    """
    if isinstance(env_or_cr, api.Environment):
        cr = env_or_cr.cr
    else:
        cr = env_or_cr

    # On a fresh install the column does not exist yet (this module adds it);
    # create it so existing rows can be backfilled.
    cr.execute("ALTER TABLE hr_leave_type ADD COLUMN IF NOT EXISTS code VARCHAR")
    cr.execute("UPDATE hr_leave_type SET code = 'LT' || id WHERE code IS NULL")
