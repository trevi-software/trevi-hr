##############################################################################
#
#    Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, timedelta

from odoo.addons.hr_contract.tests.test_contract import TestHrContracts


class TestContract(TestHrContracts):

    @classmethod
    def setUpClass(cls):
        super(TestContract, cls).setUpClass()

        # -- models
        cls.Category = cls.env["hr.employee.category"]
        cls.Contract = cls.env["hr.contract"]
        cls.Employee = cls.env["hr.employee"]
        cls.Job = cls.env["hr.job"]

        # -- contract dates
        cls.dstart = datetime.now().date()
        cls.dend = (datetime.now() + timedelta(days=90)).date()
        cls.contract_data = {
            "name": "Adam",
            "employee_id": cls.employee.id,
            "job_id": False,
            "wage": 1,
            "state": "open",
            "kanban_state": "normal",
            "date_start": datetime.now().date(),
            "date_end": (datetime.now() + timedelta(days=90)).date()
        }

        # -- Categories
        cls.category_sales = cls.Category.create({"name": "Sales", "employee_ids": False})
        cls.category_it = cls.Category.create({"name": "IT", "employee_ids": False})
        cls.category_marketing = cls.Category.create({"name": "Marketing", "employee_ids": False})
        cls.category_management = cls.Category.create({"name": "Management", "employee_ids": False})
        cls.category_consultant = cls.Category.create({"name": "Consultant", "employee_ids": False})

        # -- Jobs
        cls.job_mkt_director = cls.Job.create({
            "name": "Marketing Director",
            "category_ids": [(4, cls.category_marketing.id)],
        })
        cls.job_ux_designer = cls.Job.create({
            "name": "UX Designer",
            "category_ids": [(4, cls.category_it.id)],
        })
        cls.job_sale_associate = cls.Job.create({
            "name": "Sales Associate",
            "category_ids": [(4, cls.category_sales.id)],
        })
        cls.job_store_manager = cls.Job.create({
            "name": "Store Manager",
            "category_ids": [(4, cls.category_sales.id)],
        })
        cls.job_product_manager = cls.Job.create({
            "name": "Product Manager",
            "category_ids": [(4, cls.category_marketing.id)],
        })
        cls.job_developer = cls.Job.create({"name": "Developer", "category_ids": False})

    def assign_category_to_job(self, category_id, job_id):
        return self.Job.browse(job_id).write({'category_ids': [(4, category_id)]})

    def assign_category_to_employee(self, category_id, employee_id):
        return self.Employee.browse(employee_id).write({'category_ids', [(4, category_id)]})

    def assign_job_to_employee(self, job_id, employee_id):
        return self.Employee.browse(employee_id).write({"job_id": job_id})

    def test_add_tag_to_employee(self):
        self.assign_job_to_employee(self.job_store_manager, self.employee.id)
        contract = self.create_contract("open", "normal", self.dstart, self.dend)
        contract._tag_employees(self.employee.id, self.job_store_manager.id)
        self.assertIn(self.category_sales, self.employee.category_ids)

    def test_remove_tag_from_employee(self):
        self.assign_job_to_employee(self.job_product_manager.id, self.employee.id)
        self.assign_category_to_job(self.category_management.id, self.job_product_manager.id)
        contract = self.create_contract("open", "normal", self.dstart, self.dend)
        contract._remove_tags(self.employee.id, self.job_product_manager.id)

        self.assertNotIn(self.category_marketing, self.employee.category_ids)
        self.assertNotIn(self.category_management, self.employee.category_ids)

    def test_add_job_tags_to_employee_on_contract_create(self):
        self.assign_category_to_job(self.category_it.id, self.job_developer.id)
        self.contract_data["employee_id"] = self.employee.id
        self.contract_data["job_id"] = self.job_developer.id
        contract = self.Contract.create(self.contract_data)

        self.assertEqual(self.job_developer, contract.job_id)
        self.assertIn(self.category_it, self.employee.category_ids)

    def test_employee_categories_change_with_job_change(self):
        self.assign_category_to_job(self.category_it.id, self.job_developer.id)
        self.assign_category_to_job(self.category_management.id, self.job_product_manager.id)

        self.contract_data["employee_id"] = self.employee.id
        self.contract_data["job_id"] = self.job_developer.id

        contract = self.Contract.create(self.contract_data)

        self.assertIn(self.category_it, self.employee.category_ids)

        contract.job_id = self.job_product_manager

        self.assertNotIn(self.category_it, self.employee.category_ids)
        self.assertIn(self.category_marketing, self.employee.category_ids)
        self.assertIn(self.category_management, self.employee.category_ids)
