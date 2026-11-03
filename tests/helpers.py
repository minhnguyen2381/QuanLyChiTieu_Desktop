from datetime import datetime

from app.domain.entities import Transaction, TransactionItem, TransactionType

START = datetime(2026, 11, 1)
END = datetime(2026, 11, 30, 23, 59, 59)


def make_transaction(type_=TransactionType.OUTFLOW, date=datetime(2026, 11, 1, 9, 30),
                     items=(("food", 100.0),), id=None, **fields):
    return Transaction(
        type=type_,
        date=date,
        items=tuple(TransactionItem(key, amount) for key, amount in items),
        id=id,
        **fields,
    )


import os
from dataclasses import replace


class FakeTransactionRepository:
    def __init__(self, transactions=()):
        self.items = {t.id: t for t in transactions}
        self.list_calls = 0
        self._next_id = 1

    def list_between(self, start, end):
        self.list_calls += 1
        matching = [t for t in self.items.values() if start <= t.date <= end]
        return sorted(matching, key=lambda t: t.date, reverse=True)

    def get(self, transaction_id):
        return self.items.get(transaction_id)

    def add(self, transaction):
        new_id = f"new{self._next_id}"
        self._next_id += 1
        self.items[new_id] = replace(transaction, id=new_id)
        return new_id

    def update(self, transaction):
        self.items[transaction.id] = transaction

    def delete(self, transaction_id):
        del self.items[transaction_id]


class FakeCategoryRepository:
    def __init__(self, keys_by_type):
        self.keys_by_type = keys_by_type
        self.calls = 0

    def list_keys(self, transaction_type):
        self.calls += 1
        return list(self.keys_by_type.get(transaction_type, []))


class FakeReceiptStorage:
    def __init__(self, fail=False):
        self.fail = fail

    def save(self, source_path):
        if self.fail:
            raise OSError("disk full")
        return f"assets/receipts/{os.path.basename(source_path)}"

    def resolve(self, stored_path):
        return stored_path or None
