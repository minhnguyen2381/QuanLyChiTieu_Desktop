"""Các cổng (Protocol) mà tầng application cần từ bên ngoài. Infrastructure/presentation implement chúng."""
from datetime import datetime
from typing import Protocol

from app.domain.entities import Transaction, TransactionType
from app.domain.summary import PeriodReport


class TransactionRepository(Protocol):
    def list_between(self, start: datetime, end: datetime) -> list[Transaction]:
        """Giao dịch trong [start, end], mới nhất trước."""

    def get(self, transaction_id: str) -> Transaction | None: ...

    def add(self, transaction: Transaction) -> str:
        """Lưu giao dịch mới, trả về id."""

    def update(self, transaction: Transaction) -> None: ...

    def delete(self, transaction_id: str) -> None: ...


class CategoryRepository(Protocol):
    def list_keys(self, transaction_type: TransactionType) -> list[str]: ...


class ReceiptStorage(Protocol):
    def save(self, source_path: str) -> str:
        """Copy ảnh vào kho, trả về đường dẫn tương đối để lưu. Lỗi -> OSError."""

    def resolve(self, stored_path: str) -> str | None:
        """Đường dẫn tuyệt đối nếu file tồn tại, ngược lại None."""


class ReportExporter(Protocol):
    def export(self, report: PeriodReport, path: str) -> None: ...
