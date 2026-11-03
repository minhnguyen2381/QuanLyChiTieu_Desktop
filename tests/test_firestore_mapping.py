import unittest
from datetime import datetime, timezone

from app.domain.entities import Transaction, TransactionItem, TransactionType
from app.infrastructure.firestore_mapping import (
    category_key_from_document, transaction_from_document, transaction_to_document,
)


class FirestoreMappingTest(unittest.TestCase):
    def test_round_trip(self):
        original = Transaction(
            type=TransactionType.OUTFLOW, date=datetime(2026, 11, 1, 9, 30),
            items=(TransactionItem("food", 100.0, "trưa"),), general_note="n", contact_person="c",
            receipt_path="assets/receipts/a.png", id="x",
        )
        document = transaction_to_document(original)
        self.assertEqual(document["items"], [{"category_key": "food", "amount": 100.0, "item_note": "trưa"}])
        self.assertEqual(document["total_amount"], 100.0)
        self.assertEqual(document["type"], "outflow")
        self.assertEqual(document["image_path"], "assets/receipts/a.png")
        self.assertNotIn("id", document)
        self.assertEqual(transaction_from_document("x", document), original)

    def test_reads_legacy_document_without_category_key(self):
        data = {
            "type": "outflow", "total_amount": 50.0,
            "items": [{"category_name": "Ăn uống", "amount": 50.0, "item_note": ""}],
            "date": datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc),
            "general_note": "", "image_path": None, "contact_person": "",
        }
        transaction = transaction_from_document("old", data)
        self.assertEqual(transaction.items[0].category_key, "food")
        self.assertEqual(transaction.receipt_path, "")
        self.assertEqual(transaction.date, datetime(2026, 11, 2, 8, 0))
        self.assertIsNone(transaction.date.tzinfo)

    def test_category_key_prefers_key_then_legacy_name(self):
        self.assertEqual(category_key_from_document({"key": "food", "name": "Ăn uống"}), "food")
        self.assertEqual(category_key_from_document({"name": "Giải trí"}), "entertainment")
        self.assertEqual(category_key_from_document({"name": "Cà phê"}), "Cà phê")


if __name__ == "__main__":
    unittest.main()
