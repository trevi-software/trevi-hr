# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013,2014 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.payroll_payslip_dictionary.models.hr_payslip import (
    BasicBrowsableObject,
)


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

    def get_payslip_vals(
        self, date_from, date_to, employee_id=False, contract_id=False
    ):
        res = super(HrPayslip, self).get_payslip_vals(
            date_from, date_to, employee_id, contract_id
        )

        # Delete old lines
        res["value"].update(
            {"benefit_line_ids": [(2, x) for x in self.benefit_line_ids.ids]}
        )

        # Boilerplate
        #

        if (not employee_id) or (not date_from) or (not date_to):
            return res
        employee = self.env["hr.employee"].browse(employee_id)
        if not self.env.context.get("contract"):
            contract_ids = employee.contract_id.ids
        else:
            if contract_id:
                contract_ids = [contract_id]
            else:
                # if we don't give the contract, then the input to fill should
                # be for all current contracts of the employee
                contract_ids = employee._get_contracts(
                    date_from=date_from, date_to=date_to
                ).ids

        if not contract_ids:
            return res
        contracts = self.env["hr.contract"].browse(contract_ids)

        # Get benefit lines
        benefit_lines = self.get_benefit_lines(contracts, date_from, date_to)
        res["value"].update(
            {
                "benefit_line_ids": benefit_lines,
            }
        )
        return res

    @api.onchange("employee_id", "date_from", "date_to")
    def onchange_employee(self):
        res = super(HrPayslip, self).onchange_employee()

        # Boilerplate
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = self.contract_id.ids
        if not self.env.context.get("contract") or not self.contract_id:
            contract_ids = employee._get_contracts(
                date_from=date_from, date_to=date_to
            ).ids
            if not contract_ids:
                return
        if not self.contract_id.struct_id:
            return
        contracts = self.env["hr.contract"].browse(contract_ids)

        # Populate Benefit lines
        benefit_lines = self.get_benefit_lines(contracts, date_from, date_to)
        write_vals = [(0, 0, v) for _k, v in benefit_lines.items()]
        self.write({"benefit_line_ids": write_vals})

        return res

    @api.model
    def get_benefit_lines(self, contracts, date_from, date_to, credit_note=False):

        employee = contracts[0].employee_id
        res = {}

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
        dSlipStart = date_from
        dSlipEnd = date_to
        d = dSlipStart
        deltaSlip = 0
        while d < dSlipEnd:
            deltaSlip += 1
            d += timedelta(days=+1)

        # Test for installation of payroll_period
        if hasattr(contracts[0], "annual_pay_periods"):
            app = contracts[0].annual_pay_periods
        else:
            app = 12

        for policy in policy_ids:

            # Calculate partial period factor relative to the policy
            dPolStart = policy.start_date
            dPolEnd = dSlipEnd
            if policy.end_date:
                dPolEnd = policy.end_date
            dS = (dPolStart > dSlipStart) and dPolStart or dSlipStart
            dE = (dPolEnd < dSlipEnd) and dPolEnd or dSlipEnd

            if (dPolEnd <= dSlipStart) or (dPolStart >= dSlipEnd):
                continue

            d = dS
            deltaPol = 0
            while d < dE:
                deltaPol += 1
                d += timedelta(days=+1)

            # Calculate advantage
            #
            adv_amount = policy.calculate_advantage(dE)

            # Calculate premium
            #
            prm_amount = policy.calculate_premium(dE, app, refund=credit_note)

            res[policy.benefit_id.code]["qty"] += 1
            res[policy.benefit_id.code]["ppf"] += float(deltaPol) / float(deltaSlip)
            res[policy.benefit_id.code]["earnings"] += adv_amount
            res[policy.benefit_id.code]["deductions"] += prm_amount

        return res

    def record_benefit_premium_payments(self, benefits):

        policy_obj = self.env["hr.benefit.policy"]
        premium_obj = self.env["hr.benefit.premium.payment"]
        for payslip in self:
            for k, v in benefits.items():
                pol_ids = policy_obj.search(
                    [
                        ("employee_id", "=", payslip.employee_id.id),
                        ("benefit_id", "=", v["id"]),
                    ]
                )
                if len(pol_ids) == 0:
                    UserError(
                        _(
                            "Error creating benefit premium payment records!"
                            "Unable to find a valid benefit policy:\nEmployee: %s\nBenefit: %s"
                        )
                        % (payslip.employee_id.name, k)
                    )

                premium_obj.create(
                    {
                        "payslip_id": payslip.id,
                        "date": payslip.date_to,
                        "employee_id": payslip.employee_id.id,
                        "policy_id": pol_ids[0],
                        "amount": payslip.credit_note and -v["amount"] or v["amount"],
                    }
                )
        return

    def remove_benefit_premium_payments(self):

        pay_obj = self.env["hr.benefit.premium.payment"]
        pay_ids = pay_obj.search([("payslip_id", "in", self.ids)])
        pay_ids.unlink()

        return

    def finalize_benefit_premium_payments(self):

        payments = self.mapped("premium_payment_ids")
        payments.state_done()

    def refund_sheet(self):

        res = super(HrPayslip, self).refund_sheet()
        payments = self.mapped("premium_payment_ids")
        payments.set_cancel()

        return res

    def get_benefits_dictionary(self, contracts):
        """
        @return: returns a dictionary containing:
            * dictionaries.<CODE>.qty        - the number policies for this benefit
            * dictionaries.<CODE>.ppf        - the ppf of policy with respect to payslip
            * dictionaries.<CODE>.deductions - the amount to deduct or 0
            * dictionaries.<CODE>.earnings   - the earning amount or 0
        """

        self.ensure_one()
        res = {}

        for line in self.benefit_line_ids:
            res.update(
                {
                    line.code: BasicBrowsableObject(
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

    def get_localdict(self, contracts):

        res = super().get_localdict(contracts)
        res.update(self.get_benefits_dictionary(contracts))
        return res
