# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def get_inputs(self, contracts, date_from, date_to):

        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)

        psa_ids = self.env["hr.payslip.amendment"].search(
            [
                ("employee_id", "=", contracts[0].employee_id.id),
                ("state", "not in", ["draft, cancel, done"]),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
            ]
        )
        for line in res:

            # Pay Slip Amendment modifications
            for psa in psa_ids.filtered(
                lambda self: self.input_id.code == line["code"]
            ):

                # count the number of times this input rule appears (this
                # is dependent on no. of contracts in pay period), and
                # distribute the total amount equally among them.
                #
                rule_count = 0
                _input_contract_ids = []
                for _l2 in res:
                    if _l2["code"] == psa.input_id.code:
                        rule_count += 1
                        if _l2["contract_id"] not in _input_contract_ids:
                            _input_contract_ids.append(_l2["contract_id"])
                if line.get("amount", "x") == "x":
                    line["amount"] = 0
                if line.get("amount", False):
                    line["amount"] += psa.amount / float(rule_count)
                else:
                    line.update({"amount": psa.amount / float(rule_count)})
                psa.do_done()

        return res
