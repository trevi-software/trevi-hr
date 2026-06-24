# Copyright (C) 2022 Trevi Software (https://trevi.et)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestScheduleGroup(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Resource = cls.env["resource.resource"]
        cls.ScheduleGroup = cls.env["resource.schedule.group"]

        cls.groupKitchen = cls.ScheduleGroup.create({"name": "Kitchen A"})

    def test_default_company(self):

        self.assertEqual(
            self.groupKitchen.company_id,
            self.env.company,
            "A new record has a company by default",
        )

    def test_compute_template_count(self):

        self.assertEqual(
            self.ScheduleGroup.template_count, 0, "Initial resource count is zero"
        )

        tpl = self.env.ref("resource_schedule.attendance_template_0")
        tpl.schedule_group_ids = [(6, 0, [self.groupKitchen.id])]
        self.assertEqual(
            self.groupKitchen.template_count,
            1,
            "After adding one record resource count is 1",
        )
