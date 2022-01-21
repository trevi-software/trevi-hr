# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestContract(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestContract, cls).setUpClass()

        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrContract = cls.env["hr.contract"]
        cls.Job = cls.env["hr.job"]
        cls.Dept = cls.env["hr.department"]
        cls.employee = cls.HrEmployee.create({"name": "John"})
        cls.test_contract = dict(
            name="Test", wage=1, employee_id=cls.employee.id, state="draft"
        )
        cls.dept_rnd = cls.Dept.create({"name": "R&D"})
        cls.job_ux_designer = cls.Job.create(
            {
                "name": "#UX Designer",
                "department_id": cls.dept_rnd.id,
            }
        )

    def create_contract(self, start, end=None, trial_end=None, state="draft"):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": self.employee.id,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
                "job_id": self.job_ux_designer.id,
                "state": state,
            }
        )

    def apply_cron(self):
        self.env.ref(
            "hr_contract.ir_cron_data_contract_update_state"
        ).method_direct_trigger()

    def test_new_contract(self):
        """Creation of employee contract sets department and job"""

        self.assertFalse(self.employee.job_id)
        self.assertFalse(self.employee.department_id)

        start = datetime.now().date()
        contract = self.create_contract(start)
        contract.signal_confirm()

        self.assertEqual(self.job_ux_designer, self.employee.job_id)
        self.assertEqual(self.dept_rnd, self.employee.department_id)

    def test_new_contract_sets_contract_id(self):
        """Creation of employee contract sets link to contract"""

        self.assertFalse(self.employee.contract_id)

        start = date.today()
        trial_end = date.today() + relativedelta(days=60)
        contract = self.create_contract(start, trial_end=trial_end)
        contract.signal_confirm()

        self.assertEqual(contract, self.employee.contract_id)

    def test_consecutive_contracts(self):
        """List of contracts in period includes 'closed' contracts"""

        start = date(2021, 1, 1)
        end = date(2021, 1, 14)
        jan_end = date(2021, 1, 31)
        start2 = start + relativedelta(days=14)
        cc1 = self.create_contract(start, end=end, state="close")
        cc2 = self.create_contract(start2)
        cc2.signal_confirm()
        contracts = self.employee._get_contracts(start, jan_end)
        self.assertEqual(cc1.state, "close", "Contract 1 has ended")

        self.assertIn(cc1, contracts, "Contract 1 (closed) is in list of contracts")
        self.assertIn(cc1, contracts, "Contract 2 (open) is in list of contracts")
