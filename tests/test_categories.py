import unicodedata
import unittest

from app.domain.categories import (
    DEFAULT_CATEGORIES, LEGACY_NAME_TO_KEY, is_legacy_name, legacy_name_to_key,
)


class LegacyNameToKeyTest(unittest.TestCase):
    def test_maps_every_seeded_vietnamese_name(self):
        # Copy nguyên văn từ database/db_manager.py (baseline a2c701f)
        seeded = {
            "Lương": "salary", "Thưởng": "bonus", "Thu nhập thụ động": "passive_income",
            "Bán hàng": "sales", "Khác": "other", "Ăn uống": "food", "Hóa đơn": "bills",
            "Di chuyển": "transport", "Mua sắm": "shopping", "Sức khỏe": "health",
            "Giải trí": "entertainment",
        }
        for name, key in seeded.items():
            self.assertEqual(legacy_name_to_key(name), key, name)

    def test_decomposed_unicode_still_matches(self):
        self.assertEqual(legacy_name_to_key(unicodedata.normalize("NFD", "Ăn uống")), "food")

    def test_unknown_name_becomes_its_own_key(self):
        self.assertEqual(legacy_name_to_key("Cà phê"), "Cà phê")
        self.assertFalse(is_legacy_name("Cà phê"))

    def test_missing_name_becomes_other(self):
        self.assertEqual(legacy_name_to_key(""), "other")
        self.assertEqual(legacy_name_to_key(None), "other")

    def test_default_keys_match_legacy_mapping(self):
        defaults = {key for keys in DEFAULT_CATEGORIES.values() for key in keys}
        self.assertEqual(defaults, set(LEGACY_NAME_TO_KEY.values()))


if __name__ == "__main__":
    unittest.main()
