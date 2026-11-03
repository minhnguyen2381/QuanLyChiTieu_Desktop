import unittest

from app.domain.entities import TransactionType
from app.domain.summary import CategoryTotal, build_period_report, summarize, totals_by_category
from tests.helpers import END, START, make_transaction


class SummaryTest(unittest.TestCase):
    def setUp(self):
        self.transactions = [
            make_transaction(TransactionType.INFLOW, items=(("salary", 1000.0),)),
            make_transaction(TransactionType.OUTFLOW, items=(("food", 100.0), ("bills", 300.0))),
            make_transaction(TransactionType.OUTFLOW, items=(("food", 250.0),)),
        ]

    def test_summarize(self):
        summary = summarize(self.transactions)
        self.assertEqual((summary.inflow, summary.outflow, summary.balance), (1000.0, 650.0, 350.0))

    def test_summarize_empty(self):
        self.assertEqual(summarize([]).balance, 0)

    def test_totals_by_category_groups_filters_and_sorts_descending(self):
        self.assertEqual(
            totals_by_category(self.transactions, TransactionType.OUTFLOW),
            [CategoryTotal("food", 350.0), CategoryTotal("bills", 300.0)],
        )

    def test_build_period_report(self):
        report = build_period_report(START, END, self.transactions)
        self.assertEqual(report.summary.outflow, 650.0)
        self.assertEqual(report.inflow_by_category, [CategoryTotal("salary", 1000.0)])
        self.assertEqual((report.start, report.end), (START, END))


if __name__ == "__main__":
    unittest.main()
