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
    # Calendar sync settings
    "calendar_provider": "none",  # none, google, outlook
    "calendar_connected": False,
    "google_credentials_path": "",
    "outlook_client_id": "",
    "outlook_client_secret": "",
    "outlook_tenant_id": "",
    "calendar_auto_sync": True,
    "calendar_sync_interval": 15,  # minutes
    # Emergency levels (name/color pairs)
    "emergency_levels": [
        {"name": "Low", "color": "#5c85d6"},
        {"name": "Medium", "color": "#d6b55c"},
        {"name": "High", "color": "#d65c5c"},
    ],
    # Time estimation settings
    "buffer_time_per_hour": 45,  # minutes of buffer per hour of estimated time
    # Performance settings
    "memory_limit_mb": 512,  # Max memory usage in MB
    "cpu_policy": "balanced",  # low, balanced, high
    "gpu_acceleration": True,
    # Hotkeys
    "hotkeys": {
        "quick_capture": "Ctrl+Space",
        "new_item": "Ctrl+N",
        "page_todos": "Ctrl+1",
        "page_timetable": "Ctrl+2",
        "page_memo": "Ctrl+3",
        "page_plan": "Ctrl+4",
        "search": "Ctrl+F",
        "settings": "Ctrl+,",
    },
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
