"""Dịch chuỗi giao diện. Tra theo thứ tự: ngôn ngữ hiện tại -> tiếng Việt -> chính key."""
import json
import os

from app.config import LOCALES_DIR, SETTINGS_PATH

SUPPORTED_LANGUAGES = ("vi", "en")
DEFAULT_LANGUAGE = "vi"


class Translator:
    def __init__(self, locales_dir: str, language: str = DEFAULT_LANGUAGE):
        self._locales_dir = locales_dir
        self._catalogs: dict[str, dict[str, str]] = {}
        self.language = language

    def t(self, key: str, **params) -> str:
        text = (self._catalog(self.language).get(key)
                or self._catalog(DEFAULT_LANGUAGE).get(key)
                or key)
        return text.format(**params) if params else text

    def _catalog(self, language: str) -> dict[str, str]:
        if language not in self._catalogs:
            try:
                with open(os.path.join(self._locales_dir, f"{language}.json"), encoding="utf-8") as file:
                    self._catalogs[language] = json.load(file)
            except (OSError, ValueError):
                self._catalogs[language] = {}
        return self._catalogs[language]


def load_language(settings_path: str) -> str:
    try:
        with open(settings_path, encoding="utf-8") as file:
            language = json.load(file).get("language")
    except (OSError, ValueError, AttributeError):
        return DEFAULT_LANGUAGE
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def save_language(settings_path: str, language: str) -> None:
    with open(settings_path, "w", encoding="utf-8") as file:
        json.dump({"language": language}, file)


_translator = Translator(LOCALES_DIR, load_language(SETTINGS_PATH))


def t(key: str, **params) -> str:
    return _translator.t(key, **params)


def current_language() -> str:
    return _translator.language


def set_language(language: str, persist: bool = True) -> None:
    _translator.language = language
    if persist:
        save_language(SETTINGS_PATH, language)
