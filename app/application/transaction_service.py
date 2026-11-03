"""Use case cho giao dịch: xem theo kỳ, thêm/sửa/xoá, danh mục, ảnh biên lai."""
from dataclasses import replace
from datetime import datetime

from app.application.ports import CategoryRepository, ReceiptStorage, TransactionRepository
from app.domain.entities import Transaction, TransactionType
from app.domain.summary import PeriodReport, build_period_report


class TransactionService:
    def __init__(self, transactions: TransactionRepository, categories: CategoryRepository,
                 receipts: ReceiptStorage):
        self._transactions = transactions
        self._categories = categories
        self._receipts = receipts
        self._category_cache: dict[TransactionType, list[str]] = {}

    def load_period(self, start: datetime, end: datetime) -> PeriodReport:
        """Đọc giao dịch của kỳ đúng một lần rồi tính mọi số liệu từ đó."""
        return build_period_report(start, end, self._transactions.list_between(start, end))

    def get(self, transaction_id: str) -> Transaction | None:
        return self._transactions.get(transaction_id)

    def delete(self, transaction_id: str) -> None:
        self._transactions.delete(transaction_id)

    def save(self, transaction: Transaction, new_receipt_source: str | None = None) -> str:
        """Thêm (id None) hoặc cập nhật giao dịch. Ảnh mới được lưu trước; lỗi ảnh thì không ghi gì."""
        if new_receipt_source:
            transaction = replace(transaction, receipt_path=self._receipts.save(new_receipt_source))
        if transaction.id is None:
            return self._transactions.add(transaction)
        self._transactions.update(transaction)
        return transaction.id

    def category_keys(self, transaction_type: TransactionType) -> list[str]:
        if transaction_type not in self._category_cache:
            self._category_cache[transaction_type] = self._categories.list_keys(transaction_type)
        return self._category_cache[transaction_type]

    def resolve_receipt(self, stored_path: str) -> str | None:
        return self._receipts.resolve(stored_path)
