import unittest

from app.application.report_service import NoDataError, ReportService
from app.application.transaction_service import TransactionService
from tests.helpers import (
    END, START, FakeCategoryRepository, FakeReceiptStorage, FakeTransactionRepository, make_transaction,
)


class RecordingExporter:
    def __init__(self):
        self.calls = []

    def export(self, report, path):
        self.calls.append((report, path))


def make_report_service(transactions, exporter):
    service = TransactionService(FakeTransactionRepository(transactions), FakeCategoryRepository({}),
                                 FakeReceiptStorage())
    return ReportService(service, exporter)


class ReportServiceTest(unittest.TestCase):
    def test_raises_no_data_when_period_is_empty(self):
        exporter = RecordingExporter()
        with self.assertRaises(NoDataError):
            make_report_service([], exporter).export(START, END, "out.docx")
        self.assertEqual(exporter.calls, [])

    def test_passes_period_report_to_exporter(self):
        exporter = RecordingExporter()
        make_report_service([make_transaction(id="a")], exporter).export(START, END, "out.docx")
        report, path = exporter.calls[0]
        self.assertEqual(path, "out.docx")
        self.assertEqual([t.id for t in report.transactions], ["a"])


if __name__ == "__main__":
    unittest.main()
