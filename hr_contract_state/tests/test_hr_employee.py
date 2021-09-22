# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import datetime

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

    def create_contract(self, start, end=None, trial_end=None):
        return self.env["hr.contract"].create(
            {
                "name": "Contract",
                "employee_id": self.employee.id,
                "wage": 1,
                "date_start": start,
                "trial_date_end": trial_end,
                "date_end": end,
                "job_id": self.job_ux_designer.id,
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
