# Copyright (C) 2022 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo import fields
from odoo.exceptions import UserError
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

    def test_default_date(self):
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 1,
            }
        )
        self.assertEqual(
            psa.date,
            date.today(),
            "New payslip amendment has a default date of: today()",
        )

    def test_unlink(self):
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 1,
                "date": date.today(),
            }
        )
        self.assertEqual(
            psa.state, "draft", "New payslip amendment is in 'draft' state"
        )

        psa.do_validate()
        with self.assertRaises(UserError):
            psa.unlink()

        psa.do_cancel()
        try:
            psa.unlink()
        except Exception:
            self.fail("Unexpected error when deleting a payslip amendment")

    def test_unlink_done(self):
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 1,
                "date": date.today(),
            }
        )
        self.assertEqual(
            psa.state, "draft", "New payslip amendment is in 'draft' state"
        )

        psa.do_validate()
        psa.do_done()
        with self.assertRaises(UserError):
            psa.unlink()

    def test_name(self):
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 1,
                "date": date.today(),
            }
        )
        self.assertEqual(
            psa.name_get()[0][1],
            "Sally (SALECOM)",
            "Payslip amendment name is composed of employee name and Input code",
        )

    def test_state_change(self):
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 1,
                "date": date.today(),
            }
        )
        self.assertEqual(
            psa.state, "draft", "New payslip amendment is in 'draft' state"
        )

        psa.do_cancel()
        self.assertEqual(
            psa.state, "draft", "Change state from 'draft' -> 'cancel' should FAIL!"
        )

        psa.do_done()
        self.assertEqual(
            psa.state, "draft", "Change state from 'draft' -> 'done' should FAIL!"
        )

        psa.do_validate()
        self.assertEqual(
            psa.state, "validate", "Chage state from 'draft' -> 'validate'"
        )

        psa.do_reset()
        self.assertEqual(
            psa.state,
            "validate",
            "Change state from 'validate' -> 'draft' should FAIL!",
        )

        psa.do_cancel()
        self.assertEqual(psa.state, "cancel", "Chage state from 'validate' -> 'cancel'")

        psa.do_reset()
        self.assertEqual(psa.state, "draft", "Chage state from 'cancel' -> 'draft'")

    def test_state_change_from_done(self):
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 1,
                "date": date.today(),
            }
        )
        self.assertEqual(
            psa.state, "draft", "New payslip amendment is in 'draft' state"
        )

        psa.do_validate()
        psa.do_done()

        psa.do_reset()
        self.assertEqual(
            psa.state, "done", "Chage state from 'done' -> 'draft' should FAIL!"
        )

        psa.do_cancel()
        self.assertEqual(
            psa.state, "done", "Change state from 'done' -> 'cancel' should FAIL!"
        )

    def test_done_correct_date(self):
        dstart = date(2021, 1, 1)
        dmiddle = date(2021, 1, 15)
        dend = date(2021, 1, 31)
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 100,
                "date": dmiddle,
            }
        )
        psa.do_validate()
        cc = self.create_contract(self.eeSally.id, "draft", "done", start=dstart)
        self.apply_contract_cron()
        slip = self.Payslip.create(
            {
                "name": "A Payslip",
                "employee_id": self.eeSally.id,
                "date_from": dstart,
                "date_to": dend,
            }
        )
        slip.onchange_employee()

        self.assertIn(self.rule_commision, cc.struct_id.rule_ids)

        input_lines = slip.input_line_ids.filtered(lambda self: self.code == "SALECOM")
        self.assertEqual(
            len(input_lines), 1, "There must be a payslip input line for SALECOM"
        )

        _res = fields.Float.compare(input_lines[0].amount, 100.00, precision_digits=2)
        self.assertEqual(
            _res, 0, "The Input amount should be equal to the payslip amendment"
        )
        self.assertEqual(
            psa.state, "done", "The payslip amendment must be in 'done' state"
        )

    def test_date_out_of_bounds(self):
        dstart = date(2021, 1, 1)
        dpsa = date(2021, 2, 1)
        dend = date(2021, 1, 31)
        psa = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 100,
                "date": dpsa,
            }
        )
        psa.do_validate()
        cc = self.create_contract(self.eeSally.id, "draft", "done", start=dstart)
        self.apply_contract_cron()
        slip = self.Payslip.create(
            {
                "name": "A Payslip",
                "employee_id": self.eeSally.id,
                "date_from": dstart,
                "date_to": dend,
            }
        )
        slip.onchange_employee()

        self.assertIn(self.rule_commision, cc.struct_id.rule_ids)

        input_lines = slip.input_line_ids.filtered(lambda self: self.code == "SALECOM")
        self.assertEqual(
            len(input_lines), 1, "There must be a payslip input line for SALECOM"
        )

        _res = fields.Float.compare(input_lines[0].amount, 0.00, precision_digits=2)
        self.assertEqual(_res, 0, "The Input amount should 0")
        self.assertEqual(
            psa.state, "validate", "The payslip amendment must be in 'validate' state"
        )

    def test_done_multiple_amendments(self):
        dpsa1 = date(2021, 1, 15)
        dpsa2 = date(2021, 1, 31)
        psa1 = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 100,
                "date": dpsa1,
            }
        )
        psa1.do_validate()
        psa2 = self.Amendment.create(
            {
                "employee_id": self.eeSally.id,
                "input_id": self.input_commision.id,
                "amount": 100,
                "date": dpsa2,
            }
        )
        psa2.do_validate()
        self.assertEqual(psa1.state, "validate", "Amendment 1 is in state: 'validate'")
        self.assertEqual(psa2.state, "validate", "Amendment 2 is in state: 'validate'")
        dstart = date(2021, 1, 1)
        dend = date(2021, 1, 31)
        self.create_contract(self.eeSally.id, "draft", "done", start=dstart)
        self.apply_contract_cron()
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
        _res = fields.Float.compare(input_lines[0].amount, 200.00, precision_digits=2)
        self.assertEqual(
            _res,
            0,
            "The Input amount should be equal to the sum of the amendments 200.00",
        )
        self.assertEqual(
            psa1.state, "done", "The payslip amendment (1) must be in 'done' state"
        )
        self.assertEqual(
            psa2.state, "done", "The payslip amendment (2) must be in 'done' state"
        )
