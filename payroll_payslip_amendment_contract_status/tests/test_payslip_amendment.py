# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common


class TestPayslipAmendment(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPayslipAmendment, cls).setUpClass()

        cls.Payslip = cls.env["hr.payslip"]
        cls.Amendment = cls.env["hr.payslip.amendment"]

        cls.eeSally = cls.env["hr.employee"].create({"name": "Sally"})

        cls.rule_commision = cls.env["hr.salary.rule"].create(
            {
                "name": "Commission",
                "code": "COMM",
                "category_id": cls.env.ref("payroll.ALW").id,
                "sequence": 17,
                "amount_select": "code",
                "amount_python_compute": "result = inputs.SALECOM.amount",
            }
        )
        cls.input_commision = cls.env["hr.rule.input"].create(
            {
                "name": "Sales Commission Input",
                "code": "SALECOM",
                "input_id": cls.rule_commision.id,
            }
        )

        cls.pay_struct = cls.env.ref("payroll.structure_base")
        cls.pay_struct.write({"rule_ids": [(4, cls.rule_commision.id)]})

    def create_contract(
        self, eid, state, kanban_state, start=None, end=None, trial_end=None
    ):
        if start is None:
            start = date.today()
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": eid,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
                "struct_id": self.pay_struct.id,
            }
        )

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def test_done_2_contracts(self):

        # Setup test
        #
        dstart = date(2021, 1, 1)
        dend = date(2021, 1, 31)
        dpsa = date(2021, 1, 1)
        cc1 = self.create_contract(
            self.eeSally.id, "close", "normal", dstart, dstart + relativedelta(days=10)
        )
        cc2 = self.create_contract(
            self.eeSally.id, "draft", "done", dstart + relativedelta(days=11)
        )
        self.apply_contract_cron()
        self.assertIn(self.rule_commision, cc1.struct_id.rule_ids)
        self.assertIn(self.rule_commision, cc2.struct_id.rule_ids)
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 50,
                "date": dpsa,
            }
        )
        psa.do_validate()

        # Create payslip
        slip = self.Payslip.create(
            {
                "name": "A Payslip",
                "employee_id": self.eeSally.id,
                "date_from": dstart,
                "date_to": dend,
            }
        )
        slip.onchange_employee()

        input_lines = slip.input_line_ids.filtered(lambda self: self.code == "SALECOM")
        self.assertEqual(
            len(input_lines), 2, "There must be TWO payslip input lines for SALECOM"
        )

        _res1 = fields.Float.compare(input_lines[0].amount, 25.0, precision_digits=2)
        _res2 = fields.Float.compare(input_lines[1].amount, 25.0, precision_digits=2)
        self.assertEqual(
            _res1, 0, "The Input amount should be equal to HALF the payslip amendment"
        )
        self.assertEqual(
            fields.Float.compare(_res1, _res2, precision_digits=2),
            0,
            "The Input amounts should be equal to each other",
        )
        self.assertEqual(
            psa.state, "done", "The payslip amendment must be in 'done' state"
        )
