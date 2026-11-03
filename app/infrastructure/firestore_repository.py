"""Repository Firestore. Không có test tự động (cần Firebase thật) — logic chuyển đổi nằm ở firestore_mapping."""
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore

from app.domain.categories import DEFAULT_CATEGORIES
from app.domain.entities import Transaction, TransactionType
from app.infrastructure.firestore_mapping import (
    category_key_from_document, transaction_from_document, transaction_to_document,
)


def connect(credentials_path: str):
    """Khởi tạo Firebase (một lần) và trả về Firestore client."""
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credentials.Certificate(credentials_path))
    return firestore.client()


class FirestoreTransactionRepository:
    def __init__(self, client):
        self._collection = client.collection("transactions")

    def list_between(self, start: datetime, end: datetime) -> list[Transaction]:
        query = (
            self._collection
            .where(filter=firestore.FieldFilter("date", ">=", start))
            .where(filter=firestore.FieldFilter("date", "<=", end))
            .order_by("date", direction=firestore.Query.DESCENDING)
        )
        return [transaction_from_document(doc.id, doc.to_dict()) for doc in query.stream()]

    def get(self, transaction_id: str) -> Transaction | None:
        doc = self._collection.document(transaction_id).get()
        return transaction_from_document(doc.id, doc.to_dict()) if doc.exists else None

    def add(self, transaction: Transaction) -> str:
        document = transaction_to_document(transaction) | {"created_at": datetime.now()}
        _, reference = self._collection.add(document)
        return reference.id

    def update(self, transaction: Transaction) -> None:
        document = transaction_to_document(transaction) | {"updated_at": datetime.now()}
        self._collection.document(transaction.id).update(document)

    def delete(self, transaction_id: str) -> None:
        self._collection.document(transaction_id).delete()


class FirestoreCategoryRepository:
    def __init__(self, client):
        self._collection = client.collection("categories")

    def seed_defaults_if_empty(self) -> None:
        if self._collection.limit(1).get():
            return
        for transaction_type, keys in DEFAULT_CATEGORIES.items():
            for key in keys:
                self._collection.add({"key": key, "type": transaction_type.value})

    def list_keys(self, transaction_type: TransactionType) -> list[str]:
        query = self._collection.where(filter=firestore.FieldFilter("type", "==", transaction_type.value))
        keys = [category_key_from_document(doc.to_dict()) for doc in query.stream()]
        return list(dict.fromkeys(keys))  # bỏ trùng, giữ thứ tự
