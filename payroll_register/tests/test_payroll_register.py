# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import common, new_test_user


class TestPayrollRegister(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPayrollRegister, cls).setUpClass()

        cls.Wizard = cls.env["hr.payroll.register.run"]
        cls.Register = cls.env["hr.payroll.register"]

        cls.start = datetime(2021, 1, 1)
        cls.end = datetime(2021, 1, 31)
        cls.dept1 = cls.env["hr.department"].create({"name": "Dept A"})
        cls.eeJohn = cls.env["hr.employee"].create(
            {
                "name": "John Smith",
                "department_id": cls.dept1.id,
            }
        )
        cls.pay_struct = cls.env.ref("payroll.structure_base")
        # Payroll Manager user
        cls.userPM = new_test_user(
            cls.env,
            login="hel",
            groups="base.group_user,payroll.group_payroll_manager",
            name="Payroll manager",
            email="ric@example.com",
        )

    def create_contract(
        self, eid, state, kanban_state, start, end=None, trial_end=None
    ):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": eid,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 989.92,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
                "struct_id": self.pay_struct.id,
            }
        )

    def check_denominations(self, reg, d):
        for den in reg.denomination_ids:
            key = fields.Float.round(den.denomination, 2)
            self.assertEqual(
                0,
                fields.Float.compare(d[key], den.denomination_qty, 2),
                "Denomination key: %s" % (key),
            )

    def setUpCommon(self):
        self.create_contract(self.eeJohn.id, "open", "normal", self.start.date())

    def test_no_active_id(self):
        """If 'active_id' is not in the context raise an error"""

        self.setUpCommon()
        wiz = self.Wizard.create({"department_ids": [(6, 0, [self.dept1.id])]})
        with self.assertRaises(ValidationError):
            wiz.create_payslip_runs()

    def test_no_departments(self):
        """If no departments were selected raise an error"""

        self.setUpCommon()
        reg = self.Register.create(
            {
                "date_start": self.start,
                "date_end": self.end,
            }
        )
        wiz = self.Wizard.with_context({"active_id": reg.id}).create({})
        with self.assertRaises(UserError):
            wiz.create_payslip_runs()

    def test_payroll_register_wizard(self):
        """
        Running the wizard with one department should create a payroll
        register containing a payslip run for that department.
        """

        self.setUpCommon()
        reg = self.Register.with_user(self.userPM).create(
            {
                "date_start": self.start,
                "date_end": self.end,
            }
        )
        wiz = self.Wizard.with_context({"active_id": reg.id}).create(
            {"department_ids": [(6, 0, [self.dept1.id])]}
        )
        wiz.create_payslip_runs()

        self.assertEqual(1, len(reg.run_ids))
        self.assertEqual(self.dept1.complete_name, reg.run_ids[0].name)

    def test_payroll_register_denominations(self):
        """When the wizard is run it should also create the denominations"""

        self.setUpCommon()
        reg = self.Register.create(
            {
                "date_start": self.start,
                "date_end": self.end,
            }
        )
        wiz = self.Wizard.with_context({"active_id": reg.id}).create(
            {"department_ids": [(6, 0, [self.dept1.id])]}
        )
        wiz.create_payslip_runs()

        res = {
            0.01: 2,
            0.05: 1,
            0.10: 1,
            0.25: 1,
            0.50: 1,
            1: 4,
            5: 1,
            10: 3,
            50: 1,
            100: 1,
            200: 4,
        }
        self.assertGreater(len(reg.denomination_ids), 0)
        self.check_denominations(reg, res)
