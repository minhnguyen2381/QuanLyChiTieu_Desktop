import unittest

from app.application.transaction_service import TransactionService
from app.domain.entities import TransactionType
from tests.helpers import (
    END, START, FakeCategoryRepository, FakeReceiptStorage, FakeTransactionRepository, make_transaction,
)


class TransactionServiceTest(unittest.TestCase):
    def setUp(self):
        self.repository = FakeTransactionRepository([make_transaction(id="a", items=(("food", 100.0),))])
        self.categories = FakeCategoryRepository({
            TransactionType.OUTFLOW: ["food", "bills"],
            TransactionType.INFLOW: ["salary"],
        })
        self.receipts = FakeReceiptStorage()
        self.service = TransactionService(self.repository, self.categories, self.receipts)

    def test_load_period_queries_repository_once(self):
        report = self.service.load_period(START, END)
        self.assertEqual(self.repository.list_calls, 1)
        self.assertEqual(report.summary.outflow, 100.0)
        self.assertEqual([c.category_key for c in report.outflow_by_category], ["food"])

    def test_save_without_id_adds(self):
        new_id = self.service.save(make_transaction(items=(("bills", 20.0),)))
        self.assertEqual(self.repository.get(new_id).total, 20.0)
        self.assertEqual(len(self.repository.items), 2)

    def test_save_with_id_updates(self):
        returned_id = self.service.save(make_transaction(id="a", items=(("food", 999.0),)))
        self.assertEqual(returned_id, "a")
        self.assertEqual(self.repository.get("a").total, 999.0)
        self.assertEqual(len(self.repository.items), 1)

    def test_save_stores_new_receipt_before_writing(self):
        new_id = self.service.save(make_transaction(), new_receipt_source="C:/photos/bill.png")
        self.assertEqual(self.repository.get(new_id).receipt_path, "assets/receipts/bill.png")

    def test_failed_receipt_copy_writes_nothing(self):
        self.receipts.fail = True
        with self.assertRaises(OSError):
            self.service.save(make_transaction(), new_receipt_source="bill.png")
        self.assertEqual(len(self.repository.items), 1)

    def test_category_keys_are_cached_per_type(self):
        self.service.category_keys(TransactionType.OUTFLOW)
        keys = self.service.category_keys(TransactionType.OUTFLOW)
        self.service.category_keys(TransactionType.INFLOW)
        self.assertEqual(keys, ["food", "bills"])
        self.assertEqual(self.categories.calls, 2)

    def test_delete(self):
        self.service.delete("a")
        self.assertIsNone(self.service.get("a"))


if __name__ == "__main__":
    unittest.main()
