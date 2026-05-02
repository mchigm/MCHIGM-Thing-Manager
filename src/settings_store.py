"""
Simple settings persistence for the MCHIGM Thing Manager.

Settings are stored at ~/.mchigm_thing_manager/settings.json.
"""
import base64
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any, Dict

_DEFAULTS: Dict[str, Any] = {
    "language": "en",
    "update_repo_owner": "duidui",
    "update_repo_name": "MCHIGM_s-Thing_TM-Manager",
    "auto_check_updates": True,
    "auto_update_enabled": False,
    "update_include_prerelease": False,
    "last_update_check": "",
    "last_update_version": "",
    "ai_model": "gpt-3.5-turbo",
    "ai_models": [],
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
    "auto_escalate_emergency": True,
    "timeline_hide_finished": False,
    # Time estimation settings
    "buffer_time_per_hour": 45,  # minutes of buffer per hour of estimated time
    "kanban_sort_mode": "created",
    "kanban_compact_cards": False,
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
_SECRET_FIELDS = ("ai_api_key", "outlook_client_secret")
_ENC_PREFIX = "enc:v1:"


def _settings_path() -> Path:
    config_dir = Path.home() / ".mchigm_thing_manager"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"


def _secret_key_path() -> Path:
    return _settings_path().parent / ".settings.key"


def _ensure_secure_permissions(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        # Best-effort hardening; some platforms/filesystems may not support chmod.
        pass


def _load_or_create_secret_key() -> bytes:
    key_path = _secret_key_path()
    if key_path.exists():
        raw = key_path.read_text().strip()
        if raw:
            _ensure_secure_permissions(key_path)
            return base64.urlsafe_b64decode(raw.encode("ascii"))
    key = secrets.token_bytes(32)
    key_path.write_text(base64.urlsafe_b64encode(key).decode("ascii"))
    _ensure_secure_permissions(key_path)
    return key


def _xor_stream_crypt(payload: bytes, key: bytes, nonce: bytes) -> bytes:
    out = bytearray(len(payload))
    counter = 0
    offset = 0
    while offset < len(payload):
        counter_bytes = counter.to_bytes(4, "big")
        block = hashlib.sha256(key + nonce + counter_bytes).digest()
        size = min(len(block), len(payload) - offset)
        for idx in range(size):
            out[offset + idx] = payload[offset + idx] ^ block[idx]
        offset += size
        counter += 1
    return bytes(out)


def _encrypt_secret(value: str) -> str:
    if not value:
        return ""
    key = _load_or_create_secret_key()
    nonce = secrets.token_bytes(16)
    ciphertext = _xor_stream_crypt(value.encode("utf-8"), key, nonce)
    token = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return f"{_ENC_PREFIX}{token}"


def _decrypt_secret(value: str) -> str:
    if not value:
        return ""
    if not value.startswith(_ENC_PREFIX):
        # Backward compatibility with legacy plain-text data.
        return value
    key = _load_or_create_secret_key()
    raw = base64.urlsafe_b64decode(value[len(_ENC_PREFIX) :].encode("ascii"))
    nonce, ciphertext = raw[:16], raw[16:]
    plaintext = _xor_stream_crypt(ciphertext, key, nonce)
    return plaintext.decode("utf-8")


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
    for field in _SECRET_FIELDS:
        encrypted_key = f"{field}__enc"
        if encrypted_key in data:
            try:
                data[field] = _decrypt_secret(str(data.get(encrypted_key) or ""))
            except Exception:
                data[field] = ""
        elif field in data:
            # Preserve legacy plaintext read path, but load value into memory.
            data[field] = str(data.get(field) or "")
        else:
            data[field] = ""
    return data


def save_settings(settings: Dict[str, Any]) -> None:
    """Persist settings on disk."""
    path = _settings_path()
    merged = _DEFAULTS.copy()
    merged.update(settings)
    for field in _SECRET_FIELDS:
        raw = str(merged.get(field) or "")
        merged[field] = ""
        encrypted_key = f"{field}__enc"
        if raw:
            merged[encrypted_key] = _encrypt_secret(raw)
        else:
            merged.pop(encrypted_key, None)
    path.write_text(json.dumps(merged, indent=2))
    _ensure_secure_permissions(path)
