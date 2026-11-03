"""Tính toán tổng hợp cho một kỳ: tổng thu/chi và tổng theo danh mục."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from app.domain.entities import Transaction, TransactionType


@dataclass(frozen=True)
class PeriodSummary:
    inflow: float
    outflow: float

    @property
    def balance(self) -> float:
        return self.inflow - self.outflow


@dataclass(frozen=True)
class CategoryTotal:
    category_key: str
    total: float


@dataclass(frozen=True)
class PeriodReport:
    start: datetime
    end: datetime
    transactions: list[Transaction]
    summary: PeriodSummary
    inflow_by_category: list[CategoryTotal]
    outflow_by_category: list[CategoryTotal]


def summarize(transactions: list[Transaction]) -> PeriodSummary:
    def total_of(transaction_type: TransactionType) -> float:
        return sum(t.total for t in transactions if t.type == transaction_type)

    return PeriodSummary(inflow=total_of(TransactionType.INFLOW), outflow=total_of(TransactionType.OUTFLOW))


def totals_by_category(transactions: list[Transaction], transaction_type: TransactionType) -> list[CategoryTotal]:
    totals: dict[str, float] = defaultdict(float)
    for transaction in transactions:
        if transaction.type == transaction_type:
            for item in transaction.items:
                totals[item.category_key] += item.amount
    return sorted((CategoryTotal(key, total) for key, total in totals.items()),
                  key=lambda category: category.total, reverse=True)


def build_period_report(start: datetime, end: datetime, transactions: list[Transaction]) -> PeriodReport:
    return PeriodReport(
        start=start,
        end=end,
        transactions=transactions,
        summary=summarize(transactions),
        inflow_by_category=totals_by_category(transactions, TransactionType.INFLOW),
        outflow_by_category=totals_by_category(transactions, TransactionType.OUTFLOW),
    )
