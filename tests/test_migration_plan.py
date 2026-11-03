import json
import unittest
from datetime import datetime, timezone
from tempfile import TemporaryDirectory

from scripts.migrate_category_keys import (
    MISSING_NAME, find_fractional_amounts, find_unreadable_transactions, plan_migration, write_backup,
)


class PlanMigrationTest(unittest.TestCase):
    def test_adds_key_only_to_categories_without_one(self):
        plan = plan_migration({
            "c1": {"name": "Ăn uống", "type": "outflow"},
            "c2": {"key": "food", "name": "Ăn uống", "type": "outflow"},
        }, {})
        self.assertEqual(plan.category_updates, {"c1": {"key": "food"}})

    def test_other_maps_the_same_for_inflow_and_outflow(self):
        plan = plan_migration({"c1": {"name": "Khác", "type": "inflow"},
                               "c2": {"name": "Khác", "type": "outflow"}}, {})
        self.assertEqual(plan.category_updates, {"c1": {"key": "other"}, "c2": {"key": "other"}})

    def test_adds_category_key_and_keeps_old_item_fields(self):
        plan = plan_migration({}, {"t1": {"items": [{"category_name": "Lương", "amount": 10.0, "item_note": "x"}]}})
        self.assertEqual(plan.transaction_updates, {"t1": {"items": [
            {"category_name": "Lương", "amount": 10.0, "item_note": "x", "category_key": "salary"},
        ]}})

    def test_reports_unknown_and_missing_names(self):
        plan = plan_migration({}, {"t1": {"items": [{"category_name": "Cà phê", "amount": 1.0}, {"amount": 2.0}]}})
        keys = [item["category_key"] for item in plan.transaction_updates["t1"]["items"]]
        self.assertEqual(keys, ["Cà phê", "other"])
        self.assertEqual(plan.unknown_names, {"Cà phê", MISSING_NAME})

    def test_partially_migrated_transaction_only_fills_missing_keys(self):
        plan = plan_migration({}, {"t1": {"items": [
            {"category_name": "Ăn uống", "category_key": "food", "amount": 1.0},
            {"category_name": "Thưởng", "amount": 2.0},
        ]}})
        keys = [item["category_key"] for item in plan.transaction_updates["t1"]["items"]]
        self.assertEqual(keys, ["food", "bonus"])

    def test_is_idempotent(self):
        categories = {"c1": {"name": "Lương", "type": "inflow"}}
        transactions = {"t1": {"items": [{"category_name": "Lương", "amount": 10.0}]}, "t2": {"items": []}}
        first = plan_migration(categories, transactions)
        self.assertFalse(first.is_empty)
        migrated_categories = {i: {**d, **first.category_updates.get(i, {})} for i, d in categories.items()}
        migrated_transactions = {i: {**d, **first.transaction_updates.get(i, {})} for i, d in transactions.items()}
        self.assertTrue(plan_migration(migrated_categories, migrated_transactions).is_empty)


class ReadabilityCheckTest(unittest.TestCase):
    VALID = {"type": "outflow", "date": datetime(2026, 1, 2), "items": [{"category_name": "Ăn uống", "amount": 10.0}]}

    def test_valid_legacy_doc_is_not_reported(self):
        self.assertEqual(find_unreadable_transactions({"t1": self.VALID}), {})

    def test_doc_without_items_is_reported(self):
        errors = find_unreadable_transactions({"t1": {**self.VALID, "items": []}})
        self.assertEqual(list(errors), ["t1"])
        self.assertTrue(errors["t1"].startswith("InvalidTransaction"))

    def test_doc_missing_date_is_reported(self):
        doc = {key: value for key, value in self.VALID.items() if key != "date"}
        errors = find_unreadable_transactions({"t1": doc})
        self.assertTrue(errors["t1"].startswith("KeyError"))

    def test_fractional_amounts(self):
        docs = {"a": {"items": [{"amount": 10.5}]}, "b": {"items": [{"amount": 10.0}]}, "c": {"items": [{"amount": 10}]}}
        self.assertEqual(find_fractional_amounts(docs), ["a"])


class WriteBackupTest(unittest.TestCase):
    def test_backup_contains_both_collections_with_iso_dates(self):
        with TemporaryDirectory() as folder:
            path = write_backup({"c1": {"name": "Lương"}},
                                {"t1": {"date": datetime(2026, 1, 2, tzinfo=timezone.utc)}}, folder)
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
        self.assertEqual(data["categories"], {"c1": {"name": "Lương"}})
        self.assertTrue(data["transactions"]["t1"]["date"].startswith("2026-01-02"))


if __name__ == "__main__":
    unittest.main()
