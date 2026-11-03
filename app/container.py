"""Composition root: nơi duy nhất biết implementation cụ thể (Firestore, ổ đĩa, Word)."""
from dataclasses import dataclass

from app.application.report_service import ReportService
from app.application.transaction_service import TransactionService
from app.config import BASE_DIR, FIREBASE_CREDENTIALS_PATH
from app.infrastructure.firestore_repository import (
    FirestoreCategoryRepository, FirestoreTransactionRepository, connect,
)
from app.infrastructure.receipt_storage import LocalReceiptStorage
from app.presentation.word_exporter import WordReportExporter


@dataclass(frozen=True)
class Services:
    transactions: TransactionService
    reports: ReportService


def build_services() -> Services:
    """Kết nối Firebase và nối dependency. Chạy ở thread nền của màn hình khởi động."""
    client = connect(FIREBASE_CREDENTIALS_PATH)
    categories = FirestoreCategoryRepository(client)
    categories.seed_defaults_if_empty()
    transactions = TransactionService(FirestoreTransactionRepository(client), categories,
                                      LocalReceiptStorage(BASE_DIR))
    return Services(transactions=transactions, reports=ReportService(transactions, WordReportExporter()))
