"""Thực thể nghiệp vụ: giao dịch thu/chi gồm nhiều hạng mục."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TransactionType(StrEnum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class InvalidTransaction(ValueError):
    """Giao dịch không hợp lệ: không có hạng mục, thiếu danh mục hoặc số tiền âm."""


@dataclass(frozen=True)
class TransactionItem:
    category_key: str
    amount: float
    note: str = ""


@dataclass(frozen=True)
class Transaction:
    type: TransactionType
    date: datetime
    items: tuple[TransactionItem, ...]
    general_note: str = ""
    contact_person: str = ""
    receipt_path: str = ""  # tương đối với thư mục app, vd "assets/receipts/x.png"
    id: str | None = None

    def __post_init__(self):
        if not self.items:
            raise InvalidTransaction("A transaction needs at least one item")
        for item in self.items:
            if not item.category_key.strip():
                raise InvalidTransaction("Every item needs a category")
            if item.amount < 0:
                raise InvalidTransaction("Item amounts must not be negative")

    @property
    def total(self) -> float:
        return sum(item.amount for item in self.items)
