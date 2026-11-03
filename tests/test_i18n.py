import json
import os
import unittest
from tempfile import TemporaryDirectory

from app.config import LOCALES_DIR
from app.domain.categories import DEFAULT_CATEGORIES
from app.presentation.i18n import Translator, load_language, save_language


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False)


class TranslatorTest(unittest.TestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        write_json(os.path.join(self._dir.name, "vi.json"), {"greet": "Xin chào {name}", "only_vi": "Chỉ có vi"})
        write_json(os.path.join(self._dir.name, "en.json"), {"greet": "Hello {name}"})

    def tearDown(self):
        self._dir.cleanup()

    def test_uses_current_language_with_params(self):
        self.assertEqual(Translator(self._dir.name, "en").t("greet", name="An"), "Hello An")
        self.assertEqual(Translator(self._dir.name, "vi").t("greet", name="An"), "Xin chào An")

    def test_falls_back_to_vietnamese_then_to_key(self):
        translator = Translator(self._dir.name, "en")
        self.assertEqual(translator.t("only_vi"), "Chỉ có vi")
        self.assertEqual(translator.t("missing.key"), "missing.key")


class LanguageSettingsTest(unittest.TestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        self.path = os.path.join(self._dir.name, "settings.json")

    def tearDown(self):
        self._dir.cleanup()

    def test_save_then_load(self):
        save_language(self.path, "en")
        self.assertEqual(load_language(self.path), "en")

    def test_defaults_to_vi_for_missing_broken_or_unsupported_settings(self):
        self.assertEqual(load_language(self.path), "vi")
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("{broken")
        self.assertEqual(load_language(self.path), "vi")
        write_json(self.path, {"language": "fr"})
        self.assertEqual(load_language(self.path), "vi")


class LocaleFilesTest(unittest.TestCase):
    def load(self, language):
        with open(os.path.join(LOCALES_DIR, f"{language}.json"), encoding="utf-8") as file:
            return json.load(file)

    def test_vi_and_en_have_the_same_keys(self):
        self.assertEqual(set(self.load("vi")), set(self.load("en")))

    def test_every_default_category_has_a_translation(self):
        vi = self.load("vi")
        for keys in DEFAULT_CATEGORIES.values():
            for key in keys:
                self.assertIn(f"category.{key}", vi)


if __name__ == "__main__":
    unittest.main()
