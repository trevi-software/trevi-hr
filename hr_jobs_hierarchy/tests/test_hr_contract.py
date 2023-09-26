# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .common import TestHrCommon


class TestHrContract(TestHrCommon):
    @classmethod
    def setUpClass(cls):
        super(TestHrContract, cls).setUpClass()

    def test_manager_for_contract_employee_is_set(self):
        # -- employees
        emp_SM = self.create_employee("#EMP (sales manager)")
        emp_SA = self.create_employee("#EMP (sales associate)")
        emp_SR = self.create_employee("#EMP (sales representative)")

        # -- jobs
        job_SM = self.create_job(
            name="#Sales Manager",
            department=self.dept_sales,
            is_manager=True,
            employees=emp_SM,
        )
        job_SA = self.create_job(
            name="#Sales Associate",
            parent_job=job_SM,
            department=self.dept_sales,
            employees=emp_SA,
        )
        job_SR = self.create_job(
            name="#Sales Representative",
            parent_job=job_SM,
            department=self.dept_sales,
            employees=emp_SR,
        )

        c_data_SM = self.contract_data.copy()
        c_data_SR = self.contract_data.copy()
        c_data_SA = self.contract_data.copy()

        c_data_SM.update(
            {"name": "#CONTRACT SM", "employee_id": emp_SM.id, "job_id": job_SM.id}
        )
        c_data_SR.update(
            {"name": "#CONTRACT SR", "employee_id": emp_SR.id, "job_id": job_SR.id}
        )
        c_data_SA.update(
            {"name": "#CONTRACT SA", "employee_id": emp_SA.id, "job_id": job_SA.id}
        )

        self.create_contract_multi([c_data_SA, c_data_SR, c_data_SM])

        test_contracts = self.Contract.search([("name", "like", "#CONTRACT")])
        self.assertEqual(len(test_contracts), 3)
        self.assertEqual(emp_SA.parent_id, emp_SM)
        self.assertEqual(emp_SR.parent_id, emp_SM)
