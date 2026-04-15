"""
Unit tests for src/settings_store.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import src.settings_store as ss


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _patch_path(tmp_path: Path):
    """Context manager that redirects settings to a temp file."""
    settings_file = tmp_path / "settings.json"
    return patch.object(ss, "_settings_path", return_value=settings_file)


# ---------------------------------------------------------------------------
# load_settings
# ---------------------------------------------------------------------------
class TestLoadSettings:
    def test_returns_defaults_when_file_missing(self, tmp_path):
        with _patch_path(tmp_path):
            result = ss.load_settings()
        assert result["ai_model"] == "gpt-3.5-turbo"
        assert result["ai_api_key"] == ""
        assert result["mcp_server_url"] == ""
        assert result["mcp_status"] == "disconnected"

    def test_merges_stored_values_with_defaults(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps({"ai_model": "claude-3-haiku", "ai_api_key": "sk-abc"}))
        with patch.object(ss, "_settings_path", return_value=settings_file):
            result = ss.load_settings()
        assert result["ai_model"] == "claude-3-haiku"
        assert result["ai_api_key"] == "sk-abc"
        # Default keys that were NOT in the file should still be present
        assert result["mcp_server_url"] == ""

    def test_falls_back_to_defaults_on_corrupt_json(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("NOT VALID JSON }{")
        with patch.object(ss, "_settings_path", return_value=settings_file):
            result = ss.load_settings()
        assert result["ai_model"] == "gpt-3.5-turbo"

    def test_falls_back_to_defaults_when_json_is_not_dict(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps([1, 2, 3]))
        with patch.object(ss, "_settings_path", return_value=settings_file):
            result = ss.load_settings()
        assert result["ai_model"] == "gpt-3.5-turbo"

    def test_all_default_keys_present(self, tmp_path):
        with _patch_path(tmp_path):
            result = ss.load_settings()
        for key in ss._DEFAULTS:
            assert key in result, f"Default key {key!r} missing from load_settings() output"

    def test_calendar_defaults(self, tmp_path):
        with _patch_path(tmp_path):
            result = ss.load_settings()
        assert result["language"] == "en"
        assert result["auto_check_updates"] is True
        assert result["auto_update_enabled"] is False
        assert result["update_include_prerelease"] is False
        assert result["update_repo_owner"] == "duidui"
        assert result["update_repo_name"] == "MCHIGM_s-Thing_TM-Manager"
        assert result["calendar_provider"] == "none"
        assert result["calendar_connected"] is False
        assert result["calendar_auto_sync"] is True
        assert result["calendar_sync_interval"] == 15
        assert result["emergency_levels"]


# ---------------------------------------------------------------------------
# save_settings
# ---------------------------------------------------------------------------
class TestSaveSettings:
    def test_persists_values(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        with patch.object(ss, "_settings_path", return_value=settings_file):
            ss.save_settings({"ai_model": "gpt-4o", "ai_api_key": "sk-xyz"})
            result = ss.load_settings()
        assert result["ai_model"] == "gpt-4o"
        assert result["ai_api_key"] == "sk-xyz"

    def test_write_is_valid_json(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        with patch.object(ss, "_settings_path", return_value=settings_file):
            ss.save_settings({"ai_model": "test"})
        data = json.loads(settings_file.read_text())
        assert isinstance(data, dict)
        assert data["ai_model"] == "test"

    def test_saved_data_includes_defaults_for_missing_keys(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        with patch.object(ss, "_settings_path", return_value=settings_file):
            ss.save_settings({"ai_api_key": "key123"})
        data = json.loads(settings_file.read_text())
        # Default keys should be present
        assert "ai_model" in data
        assert data["ai_model"] == "gpt-3.5-turbo"

    def test_round_trip(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        payload = {
            "ai_model": "claude-3-opus",
            "ai_api_key": "sk-test",
            "mcp_server_url": "http://localhost:8080",
            "calendar_provider": "google",
        }
        with patch.object(ss, "_settings_path", return_value=settings_file):
            ss.save_settings(payload)
            loaded = ss.load_settings()
        for k, v in payload.items():
            assert loaded[k] == v
