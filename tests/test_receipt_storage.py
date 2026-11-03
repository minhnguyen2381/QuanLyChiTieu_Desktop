import os
import unittest
from tempfile import TemporaryDirectory

from app.infrastructure.receipt_storage import LocalReceiptStorage


class LocalReceiptStorageTest(unittest.TestCase):
    def setUp(self):
        self._base = TemporaryDirectory()
        self._sources = TemporaryDirectory()
        self.base = self._base.name
        self.storage = LocalReceiptStorage(self.base)
        self.source = os.path.join(self._sources.name, "bill.png")
        with open(self.source, "wb") as file:
            file.write(b"img")

    def tearDown(self):
        self._base.cleanup()
        self._sources.cleanup()

    def test_save_copies_file_and_returns_relative_path(self):
        stored = self.storage.save(self.source)
        self.assertTrue(stored.startswith("assets/receipts/"))
        self.assertTrue(stored.endswith("_bill.png"))
        self.assertEqual(self.storage.resolve(stored), os.path.normpath(os.path.join(self.base, stored)))

    def test_save_missing_source_raises_oserror(self):
        with self.assertRaises(OSError):
            self.storage.save(os.path.join(self.base, "missing.png"))

    def test_resolve_absolute_path(self):
        self.assertEqual(self.storage.resolve(self.source), os.path.normpath(self.source))

    def test_resolve_empty_or_missing_returns_none(self):
        self.assertIsNone(self.storage.resolve(""))
        self.assertIsNone(self.storage.resolve("assets/receipts/missing.png"))


if __name__ == "__main__":
    unittest.main()
