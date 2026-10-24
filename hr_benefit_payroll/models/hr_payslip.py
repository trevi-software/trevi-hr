# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import api, fields, models

from odoo.addons.payroll.models.hr_payslip import BaseBrowsableObject


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    benefit_line_ids = fields.One2many(
        string="Benefits", comodel_name="hr.payslip.benefit", inverse_name="payslip_id"
    )
    premium_payment_ids = fields.One2many(
        string="Benefit Premium Payments",
        comodel_name="hr.benefit.premium.payment",
        inverse_name="payslip_id",
    )

    @api.onchange("date_from", "date_to")
    def onchange_dates(self):
        for rec in self:
            if not rec.date_from or not rec.date_to:
                continue
            rec.benefit_line_ids.unlink()
            benefit_lines_dict = rec.get_benefit_lines(
                rec._get_employee_contracts(), rec.date_from, rec.date_to
            )
            write_vals = [(0, 0, v) for _k, v in benefit_lines_dict.items()]
            rec.benefit_line_ids = write_vals

        return super().onchange_dates()

    def get_payslip_vals(
        self, date_from, date_to, employee_id=False, contract_id=False, struct_id=False
    ):
        res = super().get_payslip_vals(
            date_from, date_to, employee_id, contract_id, struct_id
        )
        values = res.setdefault("value", {})

        # Delete the lines of a previous computation and create one line per
        # benefit for the new period. ``benefit_line_ids`` is a One2many, so the
        # values must be a list of (command) tuples, not the dict keyed by
        # benefit code returned by ``get_benefit_lines``.
        contracts = self._get_employee_contracts()
        if not contracts:
            # ``self`` is usually an empty recordset when the wizard builds new
            # payslips; fall back to the contract ``super()`` selected for the
            # employee so the benefit lines are generated for the new payslip.
            contracts = self.env["hr.version"].browse(values.get("contract_id") or [])
        benefit_lines = self.get_benefit_lines(contracts, date_from, date_to)
        values["benefit_line_ids"] = [
            (2, line_id) for line_id in self.benefit_line_ids.ids
        ] + [(0, 0, vals) for vals in benefit_lines.values()]
        return res

    @api.model
    def get_benefit_lines(self, contracts, date_from, date_to, credit_note=False):
        res = {}
        if not contracts:
            return res
        employee = contracts[0].employee_id

        # Search policies for those employees that are linked to payroll
        policy_ids = self.env["hr.benefit.policy"].search(
            [
                ("employee_id", "=", employee.id),
                ("benefit_id.link2payroll", "=", True),
                ("start_date", "<=", date_to),
                "|",
                ("end_date", "=", False),
                ("end_date", ">=", date_from),
            ]
        )
        benefit_ids = policy_ids.mapped("benefit_id")
        for bd in benefit_ids:
            res.update(
                {
                    bd.code: {
                        "code": bd.code,
                        "name": bd.name,
                        "qty": 0,
                        "ppf": 0,
                        "earnings": 0,
                        "deductions": 0,
                    }
                }
            )

        # One dict per benefit
        #
        d_slip_start = date_from
        d_slip_end = date_to
        d = d_slip_start
        delta_slip = 0
        while d <= d_slip_end:
            delta_slip += 1
            d += timedelta(days=+1)

        # Test for installation of payroll_period
        if hasattr(contracts[0], "annual_pay_periods"):
            app = contracts[0].annual_pay_periods
        else:
            app = 12

        for policy in policy_ids:
            # Calculate partial period factor relative to the policy
            d_pol_start = policy.start_date
            d_pol_end = d_slip_end
            if policy.end_date:
                d_pol_end = policy.end_date
            d_start = (d_pol_start > d_slip_start) and d_pol_start or d_slip_start
            d_end = (d_pol_end < d_slip_end) and d_pol_end or d_slip_end

            # Both boundary days belong to the payslip period, so a policy that
            # starts or ends on a boundary day still contributes for that day.
            if (d_pol_end < d_slip_start) or (d_pol_start > d_slip_end):
                continue

            d = d_start
            delta_pol = 0
            while d <= d_end:
                delta_pol += 1
                d += timedelta(days=+1)

            # Calculate advantage
            #
            adv_amount = policy.calculate_advantage(d_end)

            # Calculate premium
            #
            prm_amount = policy.calculate_premium(d_end, app, refund=credit_note)

            res[policy.benefit_id.code]["qty"] += 1
            res[policy.benefit_id.code]["ppf"] += float(delta_pol) / float(delta_slip)
            res[policy.benefit_id.code]["earnings"] += adv_amount
            res[policy.benefit_id.code]["deductions"] += prm_amount

        return res

    def _get_annual_pay_periods(self):
        contracts = self._get_employee_contracts()
        if contracts and hasattr(contracts[0], "annual_pay_periods"):
            return contracts[0].annual_pay_periods
        return 12

    def action_payslip_done(self):
        res = super().action_payslip_done()

        for payslip in self:
            payslip.record_benefit_premium_payments()
            payslip.finalize_benefit_premium_payments()

        return res

    def record_benefit_premium_payments(self):
        """Record a premium payment for each deducted benefit premium.

        Only benefits whose premium was actually deducted by a salary rule
        flagged ``has_premium_payment`` get a payment: recording one for every
        payroll-linked policy would mark premiums as paid that no rule ever
        deducted, which would then reduce or stop later deductions.
        """
        premium_obj = self.env["hr.benefit.premium.payment"]
        for payslip in self:
            rules = payslip.line_ids.salary_rule_id.filtered("has_premium_payment")
            benefit_ids = rules.mapped("benefit_id")
            if not benefit_ids:
                continue

            policy_ids = self.env["hr.benefit.policy"].search(
                [
                    ("employee_id", "=", payslip.employee_id.id),
                    ("benefit_id", "in", benefit_ids.ids),
                    ("start_date", "<=", payslip.date_to),
                    "|",
                    ("end_date", "=", False),
                    ("end_date", ">=", payslip.date_from),
                ]
            )
            app = payslip._get_annual_pay_periods()
            for policy in policy_ids:
                # The payment mirrors the premium that ``get_benefit_lines``
                # deducted for this policy; it must not be recomputed from the
                # employee and benefit, otherwise several policies of the same
                # benefit all book their payment on the first one.
                amount = policy.calculate_premium(
                    payslip.date_to, app, refund=payslip.credit_note
                )
                if payslip.credit_note:
                    amount = -amount
                if not amount:
                    continue
                premium_obj.create(
                    {
                        "payslip_id": payslip.id,
                        "date": payslip.date_to,
                        "employee_id": payslip.employee_id.id,
                        "policy_id": policy.id,
                        "amount": amount,
                    }
                )

    def remove_benefit_premium_payments(self):
        pay_obj = self.env["hr.benefit.premium.payment"]
        pay_ids = pay_obj.search([("payslip_id", "in", self.ids)])
        pay_ids.unlink()

    def finalize_benefit_premium_payments(self):
        payments = self.mapped("premium_payment_ids")
        payments.action_done()

    def refund_sheet(self):
        res = super().refund_sheet()
        payments = self.mapped("premium_payment_ids")
        if payments:
            payments.action_cancel()

        return res

    def get_benefits_dictionary(self, contracts):
        """
        @return: returns a dictionary dic:
            * hr_benefit.<CODE>.qty        - the number policies for this benefit
            * hr_benefit.<CODE>.ppf        - the ppf of policy with respect to payslip
            * hr_benefit.<CODE>.deductions - the amount to deduct or 0
            * hr_benefit.<CODE>.earnings   - the earning amount or 0
        """

        self.ensure_one()
        res = {}

        for line in self.benefit_line_ids:
            res.update(
                {
                    line.code: BaseBrowsableObject(
                        {
                            "qty": line.qty,
                            "ppf": line.ppf,
                            "deductions": line.deductions,
                            "earnings": line.earnings,
                        }
                    )
                }
            )

        return res

    def _get_baselocaldict(self, contracts):
        res = super()._get_baselocaldict(contracts)
        res.update(
            {
                "hr_benefit": BaseBrowsableObject(
                    self.get_benefits_dictionary(contracts)
                ),
            }
        )
        return res
