import unittest

from app.domain.entities import InvalidTransaction
from tests.helpers import make_transaction


class TransactionTest(unittest.TestCase):
    def test_total_sums_item_amounts(self):
        transaction = make_transaction(items=(("food", 100.0), ("bills", 50.5)))
        self.assertEqual(transaction.total, 150.5)

    def test_rejects_transaction_without_items(self):
        with self.assertRaises(InvalidTransaction):
            make_transaction(items=())

    def test_rejects_negative_amount(self):
        with self.assertRaises(InvalidTransaction):
            make_transaction(items=(("food", -1.0),))

    def test_allows_zero_amount_item(self):
        transaction = make_transaction(items=(("food", 0.0),))
        self.assertEqual(transaction.total, 0.0)

    def test_rejects_blank_category(self):
        with self.assertRaises(InvalidTransaction):
            make_transaction(items=(("   ", 10.0),))


if __name__ == "__main__":
    unittest.main()
