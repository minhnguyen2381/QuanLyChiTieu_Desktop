"""Use case xuất báo cáo cho một kỳ."""
from datetime import datetime

from app.application.ports import ReportExporter
from app.application.transaction_service import TransactionService


class NoDataError(Exception):
    """Kỳ được chọn không có giao dịch nào để xuất."""


class ReportService:
    def __init__(self, transaction_service: TransactionService, exporter: ReportExporter):
        self._transaction_service = transaction_service
        self._exporter = exporter

    def export(self, start: datetime, end: datetime, path: str) -> None:
        report = self._transaction_service.load_period(start, end)
        if not report.transactions:
            raise NoDataError
        self._exporter.export(report, path)
