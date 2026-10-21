# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests import common
from odoo.tools import str2bool

CONCURRENT_CONTRACTS_PARAM = "hr_contract_status.concurrent_contracts"


class TestResConfigSettings(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.IrConfig = cls.env["ir.config_parameter"]
        cls.HrEmployee = cls.env["hr.employee"]
        cls.HrVersion = cls.env["hr.version"]

    def create_employee(self, name="John"):
        return self.HrEmployee.create({"name": name})

    def create_contract(self, employee, start, end=None):
        return self.HrVersion.create(
            {
                "name": "Contract",
                "employee_id": employee.id,
                "wage": 1,
                "date_version": start,
                "contract_date_start": start,
                "contract_date_end": end,
            }
        )

    def assert_concurrent_contracts_allowed(self, allowed):
        param = self.IrConfig.sudo().get_param(CONCURRENT_CONTRACTS_PARAM, False)
        self.assertEqual(allowed, str2bool(param))

        employee = self.create_employee()
        start = datetime.strptime("2015-11-01", "%Y-%m-%d").date()
        end = datetime.strptime("2015-11-30", "%Y-%m-%d").date()
        self.create_contract(employee, start, end)

        # Incoming contract, overlapping the first one
        start = datetime.strptime("2015-11-15", "%Y-%m-%d").date()
        end = datetime.strptime("2015-12-30", "%Y-%m-%d").date()
        if allowed:
            self.create_contract(employee, start, end)
        else:
            with self.assertRaises(
                ValidationError,
                msg="It should not create two contracts running at the same time",
            ):
                self.create_contract(employee, start, end)

    def test_no_concurrent_contracts(self):
        """If concurrent contracts aren't enabled creating a
        second overlapping contract fails"""

        self.assert_concurrent_contracts_allowed(False)

    def test_concurrent_contracts(self):
        """If concurrent contracts are enabled creating more than
        one overlapping contract succeeds"""

        self.IrConfig.sudo().set_param(CONCURRENT_CONTRACTS_PARAM, True)

        self.assert_concurrent_contracts_allowed(True)

    def test_concurrent_contracts_setting(self):
        """The 'Allow concurrent contracts' setting drives the constraint"""

        settings = self.env["res.config.settings"].create(
            {"concurrent_contracts": True}
        )
        settings.execute()
        self.assert_concurrent_contracts_allowed(True)

        settings = self.env["res.config.settings"].create(
            {"concurrent_contracts": False}
        )
        settings.execute()
        self.assert_concurrent_contracts_allowed(False)

    def test_res_config_settings_view(self):
        """The setting is added to the HR settings form"""

        view = self.env.ref("hr_contract_status.res_config_settings_view_form")
        arch = self.env["res.config.settings"].get_views([(view.id, "form")])["views"][
            "form"
        ]["arch"]

        self.assertIn("concurrent_contracts", arch)
