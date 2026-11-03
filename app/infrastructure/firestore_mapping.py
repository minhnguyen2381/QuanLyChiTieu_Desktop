"""Chuyển đổi giữa document Firestore và entity. Tên field Firestore chỉ xuất hiện ở file này."""
from datetime import datetime

from app.domain.categories import legacy_name_to_key
from app.domain.entities import Transaction, TransactionItem, TransactionType


def transaction_to_document(transaction: Transaction) -> dict:
    return {
        "type": transaction.type.value,
        "total_amount": transaction.total,  # giữ để tương thích dữ liệu cũ
        "items": [
            {"category_key": item.category_key, "amount": item.amount, "item_note": item.note}
            for item in transaction.items
        ],
        "date": transaction.date,
        "general_note": transaction.general_note,
        "image_path": transaction.receipt_path,
        "contact_person": transaction.contact_person,
    }


def transaction_from_document(doc_id: str, data: dict) -> Transaction:
    return Transaction(
        type=TransactionType(data["type"]),
        date=_as_naive(data["date"]),
        items=tuple(_item_from_document(item) for item in data.get("items", [])),
        general_note=data.get("general_note") or "",
        contact_person=data.get("contact_person") or "",
        receipt_path=data.get("image_path") or "",
        id=doc_id,
    )


def category_key_from_document(data: dict) -> str:
    return data.get("key") or legacy_name_to_key(data.get("name"))


def _item_from_document(item: dict) -> TransactionItem:
    return TransactionItem(
        category_key=item.get("category_key") or legacy_name_to_key(item.get("category_name")),
        amount=float(item.get("amount", 0)),
        note=item.get("item_note") or "",
    )


def _as_naive(value: datetime) -> datetime:
    # App luôn ghi datetime naive (giờ máy), Firestore trả về cùng giá trị nhưng gắn UTC.
    # Bỏ tzinfo để giữ nguyên giờ hiển thị như phiên bản cũ.
    return value.replace(tzinfo=None) if value.tzinfo else value
