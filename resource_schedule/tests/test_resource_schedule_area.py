# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestScheduleArea(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Resource = cls.env["resource.resource"]
        cls.ScheduleArea = cls.env["resource.schedule.area"]

        cls.areaKitchen = cls.ScheduleArea.create({"name": "Kitchen A"})
        cls.resJohn = cls.Resource.create(
            {
                "name": "John",
            }
        )
        cls.resSally = cls.Resource.create(
            {
                "name": "Sally",
            }
        )

    def test_default_company(self):

        self.assertEqual(
            self.areaKitchen.company_id,
            self.env.company,
            "A new record has a company by default",
        )

    def test_compute_resource_count(self):

        self.assertEqual(
            self.ScheduleArea.resource_count, 0, "Initial resource count is zero"
        )

        self.resJohn.default_area_id = self.areaKitchen
        self.assertEqual(
            self.areaKitchen.resource_count,
            1,
            "After adding one record resource count is 1",
        )
