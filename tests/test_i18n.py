"""Unit tests for src/i18n.py"""

import src.i18n as i18n


class TestCurrentLanguage:
    def test_system_language_uses_system_locale(self, monkeypatch):
        monkeypatch.setattr(i18n, "load_settings", lambda: {"language": "system"})
        monkeypatch.setattr(i18n, "system_language", lambda: "zh")
        assert i18n.current_language() == "zh"

    def test_english_default_when_locale_not_supported(self, monkeypatch):
        monkeypatch.setattr(i18n, "load_settings", lambda: {"language": "system"})
        monkeypatch.setattr(i18n, "system_language", lambda: "en")
        assert i18n.current_language() == "en"


class TestLanguageChoices:
    def test_includes_system_option(self):
        values = {value for value, _ in i18n.language_choices()}
        assert "system" in values
