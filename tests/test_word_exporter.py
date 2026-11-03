import os
import unittest
from tempfile import TemporaryDirectory

from docx import Document

from app.domain.entities import TransactionType
from app.domain.summary import build_period_report
from app.presentation.i18n import set_language
from app.presentation.word_exporter import WordReportExporter
from tests.helpers import END, START, make_transaction


class WordReportExporterTest(unittest.TestCase):
    def setUp(self):
        set_language("vi", persist=False)

    def test_exports_overview_charts_and_detail_rows(self):
        report = build_period_report(START, END, [
            make_transaction(id="a"),
            make_transaction(TransactionType.INFLOW, items=(("salary", 500.0),), id="b"),
        ])
        with TemporaryDirectory() as folder:
            path = os.path.join(folder, "report.docx")
            WordReportExporter().export(report, path)
            document = Document(path)

        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        self.assertIn("BÁO CÁO QUẢN LÝ CHI TIÊU", text)
        self.assertIn("Tổng Thu: 500 đ", text)
        self.assertEqual(len(document.inline_shapes), 2)
        rows = document.tables[0].rows
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].cells[0].text, "Ngày")
        self.assertIn("Ăn uống", rows[1].cells[2].text + rows[2].cells[2].text)

    def test_exports_in_english(self):
        set_language("en", persist=False)
        report = build_period_report(START, END, [make_transaction(id="a")])
        with TemporaryDirectory() as folder:
            path = os.path.join(folder, "report.docx")
            WordReportExporter().export(report, path)
            document = Document(path)
        self.assertEqual(document.paragraphs[0].text, "EXPENSE REPORT")
        self.assertIn("Food & drinks", document.tables[0].rows[1].cells[2].text)
        set_language("vi", persist=False)


if __name__ == "__main__":
    unittest.main()
