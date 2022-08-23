# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models


class PayrollPeriodSchedule(models.Model):
    _inherit = "hr.payroll.period.schedule"

    use_operating_units = fields.Boolean(
        help="If checked create a separate payroll period for each Operating Unit"
    )

    def payroll_period_data_hook(
        self, _data=None, mo_name=False, mo_num=False, yearno=False
    ):

        # Modify the current data to be for the first OU and
        # Create a payroll period for all the rest
        #
        res = super().payroll_period_data_hook(_data)
        if self.use_operating_units:
            ou_ids = self.env["operating.unit"].search([])
            if len(ou_ids) > 0:
                res.update(
                    {
                        "operating_unit_id": ou_ids.ids[0],
                        "name": f"{res['name']} {ou_ids[0].name}",
                    }
                )
            if len(ou_ids) > 1:
                for ou in ou_ids.filtered(lambda x: x.id != res["operating_unit_id"]):
                    other_data = {
                        "name": _("{}/{} {} {}").format(
                            str(yearno), str(mo_num), str(mo_name), ou.name
                        ),
                        "schedule_id": res["schedule_id"],
                        "date_start": res["date_start"],
                        "date_end": res["date_end"],
                        "operating_unit_id": ou.id,
                    }
                    self.write({"pay_period_ids": [(0, 0, other_data)]})

        return res
