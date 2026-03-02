"""
Simple settings persistence for the MCHIGM Thing Manager.

Settings are stored at ~/.mchigm_thing_manager/settings.json.
"""
import json
from pathlib import Path
from typing import Any, Dict

_DEFAULTS: Dict[str, Any] = {
    "ai_model": "gpt-3.5-turbo",
    "ai_api_key": "",
    "mcp_server_url": "",
    "mcp_status": "disconnected",
}


def _settings_path() -> Path:
    config_dir = Path.home() / ".mchigm_thing_manager"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"


def load_settings() -> Dict[str, Any]:
    """Return settings merged with defaults."""
    path = _settings_path()
    data = _DEFAULTS.copy()
    if path.exists():
        try:
            loaded = json.loads(path.read_text())
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception:
            # Corrupt settings should not crash the app; fall back to defaults.
            pass
    return data


def save_settings(settings: Dict[str, Any]) -> None:
    """Persist settings on disk."""
    path = _settings_path()
    merged = _DEFAULTS.copy()
    merged.update(settings)
    path.write_text(json.dumps(merged, indent=2))
