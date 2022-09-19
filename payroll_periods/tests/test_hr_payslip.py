# Copyright (C) 2021 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.tests import Form

from odoo.addons.payroll.tests.common import TestPayslipBase


class TestPayslip(TestPayslipBase):
    def test_get_categories_dict(self):

        # I create an employee Payslip
        frm = Form(self.Payslip)
        frm.employee_id = self.richard_emp
        richard_payslip = frm.save()
        richard_payslip.compute_sheet()
        richard_payslip.write({"number": "SLIP/1000"})

        categories = richard_payslip.get_categories_dict()
        self.assertEqual(
            categories,
            {},
            "Salary rule categories dictionary is empty because "
            "no contracts have been approved yet",
        )
