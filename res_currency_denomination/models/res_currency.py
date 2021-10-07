# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import math

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class ResCurrencyDenomination(models.Model):

    _name = "res.currency.denomination"
    _description = "Currency Denomination"
    _rec_name = "value"

    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    ratio = fields.Float(
        help="Ratio of this denomination to the smallest integral denomination."
    )
    value = fields.Float(digits=(12, 6))


class ResCurrency(models.Model):

    _inherit = "res.currency"

    denomination_ids = fields.One2many(
        string="Denominations",
        comodel_name="res.currency.denomination",
        inverse_name="currency_id",
    )

    @api.model
    def get_denominations_from_amount(self, currency_name, amount):

        # Get denominations for currency
        # Arrange in order from largest value to smallest.
        #
        denominations = []
        smallest_note = 1
        currency_obj = self.env["res.currency"]
        currency_id = currency_obj.search([("name", "=", currency_name)])[0]

        for currency in currency_id:
            for denom in currency.denomination_ids:
                if float_compare(denom.ratio, 1.00, precision_digits=2) == 0:
                    smallest_note = denom.value

                if len(denominations) == 0:
                    denominations.append(denom.value)
                    continue

                idx = 0
                last_idx = len(denominations) - 1
                for preexist_val in denominations:
                    if denom.value > preexist_val:
                        denominations.insert(idx, denom.value)
                        break
                    elif idx == last_idx:
                        denominations.append(denom.value)
                        break
                    idx += 1

        denom_qty_list = dict.fromkeys(denominations, 0)
        cents_factor = float(smallest_note) / denominations[-1]
        cents, notes = math.modf(amount)

        notes = int(notes)
        # XXX - rounding to 4 decimal places should work for most currencies... I hope
        cents = int(round(cents, 4) * cents_factor)
        for denom in denominations:
            if notes >= denom:
                denom_qty_list[denom] += int(notes / denom)
            elif float_compare(denom, smallest_note, precision_digits=4) == 0:
                denom_qty_list[denom] += int(notes / smallest_note)
                notes = 0
            notes = (notes > 0) and (notes % denom) or 0

            if notes == 0 and cents >= (denom * cents_factor):
                cooked_denom = int(denom * cents_factor)
                if cents >= cooked_denom:
                    denom_qty_list[denom] += cents / cooked_denom
                elif denom == denominations[-1]:
                    denom_qty_list[denom] += cents / cents_factor
                    cents = 0
                cents = cents % denom

        res = []
        for k, v in denom_qty_list.items():
            vals = {
                "name": k,
                "qty": v,
            }
            res.append(vals)

        return res
