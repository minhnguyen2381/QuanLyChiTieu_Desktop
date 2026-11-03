"""Xuất báo cáo kỳ ra file Word (implement ReportExporter)."""
import io
from datetime import datetime

from docx import Document
from docx.shared import Inches
from matplotlib.figure import Figure

from app.domain.entities import Transaction, TransactionItem
from app.domain.summary import CategoryTotal, PeriodReport, PeriodSummary
from app.presentation.charts import plot_category_bars
from app.presentation.formatters import category_label, format_date, format_money, type_label
from app.presentation.i18n import t

DETAIL_COLUMNS = ("report.col_date", "report.col_type", "report.col_items", "report.col_total", "report.col_note")


class WordReportExporter:
    def export(self, report: PeriodReport, path: str) -> None:
        document = Document()
        document.add_heading(t("report.title"), 0)
        document.add_paragraph(t("report.period", start=format_date(report.start), end=format_date(report.end)))
        document.add_paragraph(t("report.exported_at", time=datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        _add_overview(document, report.summary)
        _add_charts(document, report)
        _add_detail_table(document, report.transactions)
        document.save(path)


def _add_overview(document, summary: PeriodSummary) -> None:
    document.add_heading(t("report.section_overview"), level=1)
    paragraph = document.add_paragraph()
    paragraph.add_run(t("summary.inflow", amount=format_money(summary.inflow)) + "\n").bold = True
    paragraph.add_run(t("summary.outflow", amount=format_money(summary.outflow)) + "\n").bold = True
    paragraph.add_run(t("report.balance", amount=format_money(summary.balance))).bold = True


def _add_charts(document, report: PeriodReport) -> None:
    document.add_heading(t("report.section_charts"), level=1)
    for totals, title_key, color in ((report.inflow_by_category, "chart.inflow_title", "green"),
                                     (report.outflow_by_category, "chart.outflow_title", "red")):
        document.add_picture(_chart_png(totals, t(title_key), color), width=Inches(6.0))


def _add_detail_table(document, transactions: list[Transaction]) -> None:
    document.add_heading(t("report.section_details"), level=1)
    table = document.add_table(rows=1, cols=len(DETAIL_COLUMNS))
    table.style = "Table Grid"
    for cell, key in zip(table.rows[0].cells, DETAIL_COLUMNS):
        cell.text = t(key)
    for transaction in sorted(transactions, key=lambda tr: tr.date):  # báo cáo: cũ nhất trước
        cells = table.add_row().cells
        cells[0].text = format_date(transaction.date)
        cells[1].text = type_label(transaction.type)
        cells[2].text = "\n".join(_describe_item(item) for item in transaction.items)
        cells[3].text = format_money(transaction.total)
        cells[4].text = transaction.general_note


def _describe_item(item: TransactionItem) -> str:
    purpose = t("report.item_purpose", note=item.note) if item.note else ""
    return f"- {category_label(item.category_key)}{purpose}: {format_money(item.amount)}"


def _chart_png(totals: list[CategoryTotal], title: str, color: str) -> io.BytesIO:
    figure = Figure(figsize=(8, 5))
    plot_category_bars(figure.subplots(), totals, title, color)
    figure.tight_layout()
    image = io.BytesIO()
    figure.savefig(image, format="png", bbox_inches="tight")
    image.seek(0)
    return image
