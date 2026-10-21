# Copyright (C) 2021 Trevi Software (https://trevi.et)
# Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.fields import Date
from odoo.tests import common


class TestContract(common.TransactionCase):
    """Odoo 19 merged ``hr_contract`` into ``hr`` and renamed ``hr.contract`` to
    ``hr.version``, so the upstream ``hr_contract.tests.test_contract`` base
    class no longer exists. This test builds its own fixtures instead.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # -- models
        cls.Category = cls.env["hr.employee.category"]
        cls.Version = cls.env["hr.version"]
        cls.Employee = cls.env["hr.employee"]
        cls.Job = cls.env["hr.job"]

        # -- contract dates
        cls.dstart = Date.today()
        cls.dend = Date.today() + timedelta(days=90)

        # -- employee, created with an initial version that is dated in the past
        #    so a contract version can be added later without violating the
        #    (employee_id, date_version) unique index
        cls.employee = cls.Employee.create(
            {"name": "John Doe", "date_version": "2020-01-01"}
        )

        # -- Categories
        cls.category_sales = cls.Category.create({"name": "#Sales"})
        cls.category_it = cls.Category.create({"name": "#IT"})
        cls.category_marketing = cls.Category.create({"name": "#Marketing"})
        cls.category_management = cls.Category.create({"name": "#Management"})
        cls.category_consultant = cls.Category.create({"name": "#Consultant"})

        # -- Jobs
        cls.job_mkt_director = cls.Job.create(
            {
                "name": "#Marketing Director",
                "category_ids": [(4, cls.category_marketing.id)],
            }
        )
        cls.job_ux_designer = cls.Job.create(
            {
                "name": "#UX Designer",
                "category_ids": [(4, cls.category_it.id)],
            }
        )
        cls.job_sale_associate = cls.Job.create(
            {
                "name": "#Sales Associate",
                "category_ids": [(4, cls.category_sales.id)],
            }
        )
        cls.job_store_manager = cls.Job.create(
            {
                "name": "#Store Manager",
                "category_ids": [(4, cls.category_sales.id)],
            }
        )
        cls.job_product_manager = cls.Job.create(
            {
                "name": "#Product Manager",
                "category_ids": [(4, cls.category_marketing.id)],
            }
        )
        cls.job_developer = cls.Job.create(
            {"name": "#Developer", "category_ids": False}
        )

    def create_contract(self, start, end=None, job_id=False, employee_id=None):
        return self.Version.create(
            {
                "name": "Contract #1",
                "employee_id": employee_id or self.employee.id,
                "job_id": job_id,
                "wage": 1,
                "date_version": start,
                "contract_date_start": start,
                "contract_date_end": end,
            }
        )

    def assign_category_to_job(self, category_id, job_id):
        return self.Job.browse(job_id).write({"category_ids": [(4, category_id)]})

    def assign_category_to_employee(self, category_id, employee_id):
        return self.Employee.browse(employee_id).write(
            {"category_ids": [(4, category_id)]}
        )

    def assign_job_to_employee(self, job_id, employee_id):
        return self.Employee.browse(employee_id).write({"job_id": job_id})

    def test_add_tag_to_employee(self):
        self.assign_job_to_employee(self.job_store_manager, self.employee.id)
        contract = self.create_contract(self.dstart, self.dend)
        contract._tag_employees(self.employee.id, self.job_store_manager.id)
        self.assertIn(self.category_sales, self.employee.category_ids)

    def test_remove_tag_from_employee(self):
        self.assign_job_to_employee(self.job_product_manager.id, self.employee.id)
        self.assign_category_to_employee(self.category_marketing.id, self.employee.id)
        self.assign_category_to_job(
            self.category_management.id, self.job_product_manager.id
        )
        contract = self.create_contract(self.dstart, self.dend)
        contract._remove_tags(self.employee.id, self.job_product_manager.id)

        self.assertNotIn(self.category_marketing, self.employee.category_ids)
        self.assertNotIn(self.category_management, self.employee.category_ids)

    def test_add_job_tags_to_employee_on_contract_create(self):
        self.assign_category_to_job(self.category_it.id, self.job_developer.id)
        contract = self.create_contract(
            self.dstart, self.dend, job_id=self.job_developer.id
        )

        self.assertEqual(self.job_developer, contract.job_id)
        self.assertIn(self.category_it, self.employee.category_ids)

    def test_employee_categories_change_with_job_change(self):
        self.assign_category_to_job(self.category_it.id, self.job_developer.id)
        self.assign_category_to_job(
            self.category_management.id, self.job_product_manager.id
        )

        contract = self.create_contract(
            self.dstart, self.dend, job_id=self.job_developer.id
        )

        self.assertIn(self.category_it, self.employee.category_ids)

        contract.job_id = self.job_product_manager

        self.assertNotIn(self.category_it, self.employee.category_ids)
        self.assertIn(self.category_marketing, self.employee.category_ids)
        self.assertIn(self.category_management, self.employee.category_ids)
