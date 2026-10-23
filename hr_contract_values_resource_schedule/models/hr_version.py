# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrVersion(models.Model):
    """Seed a new employee contract with the working hours taken from the
    latest ``hr.contract.init`` record.

    In Odoo 19 ``hr_contract`` was merged into ``hr`` and ``hr.contract`` was
    renamed to ``hr.version``.
    """

    _inherit = "hr.version"

    @api.model
    def _get_resource_calendar(self):
        res = self.env.company.resource_calendar_id.id
        init = self.get_latest_initial_values()
        if init is not None and init.resource_calendar_id:
            res = init.resource_calendar_id.id
        return res

    # ``hr.version`` already declares ``resource_calendar_id`` along with its
    # own ``_inverse_resource_calendar_id`` (which keeps the working hours of
    # the employee's current version in sync with its resource), so only the
    # default is overridden here: field definitions are merged on inheritance
    # and the core attributes (inverse, string, check_company, tracking) are
    # preserved.  The employee's resource is therefore synced by the core
    # inverse, which correctly limits the update to the current version;
    # writing the employee resource for every created version here would change
    # the employee's live working hours when a future-dated or historical
    # version is created.
    resource_calendar_id = fields.Many2one(
        comodel_name="resource.calendar",
        default=lambda self: self._get_resource_calendar(),
    )
