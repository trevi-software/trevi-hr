# Copyright (C) 2022 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from dateutil.relativedelta import relativedelta

from . import common


class TestPolicy(common.TestPolicyCommon):
    def test_get_latest_policy(self):

        pMarch = self.Policy.create(
            {"name": "P1", "date": date(2020, 3, 1), "tz": "UTC"}
        )
        pDec = self.Policy.create(
            {"name": "P1", "date": date(2020, 12, 1), "tz": "UTC"}
        )
        pJan = self.Policy.create({"name": "P1", "date": date(2020, 1, 1), "tz": "UTC"})
        pg = self.PolicyGroup.create(
            {
                "name": "PGroup",
                "rounding_policy_ids": [(6, 0, [pDec.id, pMarch.id, pJan.id])],
            }
        )
        ap = self.Policy.get_latest_policy(pg, date.today())

        self.assertEqual(ap, pDec, "I got the latest policy from available ones")

    def test_get_latest_policy_with_future(self):

        pastDate = date.today() - relativedelta(days=5)
        futureDate = date.today() + relativedelta(days=1)
        pFuture = self.Policy.create({"name": "PF", "date": futureDate, "tz": "UTC"})
        pPast = self.Policy.create({"name": "PP", "date": pastDate, "tz": "UTC"})
        pg = self.PolicyGroup.create(
            {
                "name": "PGroup",
                "rounding_policy_ids": [(6, 0, [pFuture.id, pPast.id])],
            }
        )
        ap = self.Policy.get_latest_policy(pg, date.today())

        self.assertEqual(ap, pPast, "The lastest policy is not in the future")
