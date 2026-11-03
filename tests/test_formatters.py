import unittest
from datetime import date, datetime

from app.domain.entities import TransactionType
from app.presentation.formatters import (
    category_label, combine_date_keep_time, format_date, format_money, parse_money, type_label,
)
from app.presentation.i18n import set_language


class FormattersTest(unittest.TestCase):
    def setUp(self):
        set_language("vi", persist=False)

    def tearDown(self):
        set_language("vi", persist=False)

    def test_format_money_per_language(self):
        self.assertEqual(format_money(1500000, "vi"), "1.500.000 đ")
        self.assertEqual(format_money(1500000, "en"), "1,500,000 VND")
        self.assertEqual(format_money(-2000, "vi"), "-2.000 đ")

    def test_format_money_uses_current_language_by_default(self):
        set_language("en", persist=False)
        self.assertEqual(format_money(1000), "1,000 VND")

    def test_parse_money_accepts_both_styles(self):
        for text in ("1.500.000 đ", "1,500,000 VND", "1500000", " 1 500 000 "):
            self.assertEqual(parse_money(text), 1500000.0, text)
        self.assertEqual(parse_money(""), 0.0)
        self.assertEqual(parse_money("abc"), 0.0)

    def test_category_label_translates_known_keys_and_keeps_custom(self):
        self.assertEqual(category_label("food"), "Ăn uống")
        self.assertEqual(category_label("Cà phê"), "Cà phê")
        set_language("en", persist=False)
        self.assertEqual(category_label("food"), "Food & drinks")

    def test_type_label(self):
        self.assertEqual(type_label(TransactionType.INFLOW), "Thu")

    def test_format_date(self):
        self.assertEqual(format_date(datetime(2026, 1, 5, 10, 0)), "05/01/2026")

    def test_combine_date_keeps_original_time(self):
        result = combine_date_keep_time(date(2026, 11, 5), datetime(2026, 10, 1, 14, 25, 7))
        self.assertEqual(result, datetime(2026, 11, 5, 14, 25, 7))

    def test_combine_date_without_original_uses_given_date(self):
        self.assertEqual(combine_date_keep_time(date(2026, 11, 5), None).date(), date(2026, 11, 5))


if __name__ == "__main__":
    unittest.main()
