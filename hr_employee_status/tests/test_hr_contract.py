# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestEmployee(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestEmployee, cls).setUpClass()

        cls.Employee = cls.env["hr.employee"]
        cls.Contract = cls.env["hr.contract"]
        cls.ContractEnd = cls.env["hr.contract.end"]
        cls.Separation = cls.env["hr.employee.termination"]
        cls.reason = cls.env["hr.employee.termination.reason"].create(
            {"name": "Retired"}
        )

    def create_employee(self, name="John Smith"):
        return self.Employee.create(
            {
                "name": name,
            }
        )

    def apply_contract_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def create_contract(
        self, employee, state, kanban_state, start, end=None, trial_end=None
    ):
        return self.Contract.create(
            {
                "name": "Contract",
                "employee_id": employee.id,
                "state": state,
                "kanban_state": kanban_state,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
            }
        )

    def test_contract_autoclose(self):
        """Closing a contract with automated action causes separation record to be created."""

        start = date.today() - relativedelta(days=100)
        end = date.today() - relativedelta(days=1)
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start, end)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # Auto-close contract
        self.apply_contract_cron()

        self.assertEqual(1, len(ee.inactive_ids))
        self.assertEqual(end, ee.inactive_ids[0].name)
        self.assertEqual("separation", ee.status)
        self.assertEqual(end, cc.date_end)
        self.assertEqual("close", cc.state)

    def test_end_contract_wizard(self):
        """Running 'End Contract' wizard creates separation record and closes contract"""

        start = date.today() - relativedelta(days=100)
        end = date.today()
        ee = self.create_employee()
        cc = self.create_contract(ee, "draft", "done", start)
        cc.signal_confirm()
        self.assertEqual("open", cc.state)
        self.assertEqual("active", ee.status)

        # End Contract wizard
        cend = self.ContractEnd.create(
            {
                "contract_id": cc.id,
                "employee_id": ee.id,
                "reason_id": self.reason.id,
                "date": date.today(),
            }
        )
        cend.set_employee_inactive()

        self.assertEqual(1, len(ee.inactive_ids))
        self.assertEqual(end, ee.inactive_ids[0].name)
        self.assertEqual("separation", ee.status)
        self.assertEqual(end, cc.date_end)
        self.assertEqual("close", cc.state)
