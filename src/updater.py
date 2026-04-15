"""
Auto-update helpers for checking GitHub releases.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import platform
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_VERSION_RE = re.compile(r"^v?(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?")


@dataclass
class UpdateCheckResult:
    success: bool
    has_update: bool
    message: str
    current_version: str
    latest_version: str = ""
    release_url: str = ""
    download_url: str = ""
    checked_at: str = ""


def _parse_version(raw: str) -> tuple[int, int, int]:
    match = _VERSION_RE.match((raw or "").strip())
    if not match:
        raise ValueError(f"Invalid version format: {raw!r}")
    return (
        int(match.group("major") or 0),
        int(match.group("minor") or 0),
        int(match.group("patch") or 0),
    )


def is_newer_version(current_version: str, latest_version: str) -> bool:
    return _parse_version(latest_version) > _parse_version(current_version)


def _fetch_json(url: str, timeout: int = 8) -> dict | list:
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "mchigm-thing-manager-updater",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Update server error ({exc.code}).") from exc
    except URLError as exc:
        raise RuntimeError(f"Unable to reach update server: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("Update check timed out.") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid update payload.") from exc


def _asset_download_url(release: dict) -> str:
    assets = release.get("assets") or []
    if not assets:
        return ""
    system = platform.system().lower()
    preferred_tokens = ["zip", "tar.gz"]
    if system == "darwin":
        preferred_tokens = ["pkg", "dmg", "zip", "tar.gz"]
    elif system == "windows":
        preferred_tokens = ["setup.exe", ".exe", ".msi", "zip"]
    elif system == "linux":
        preferred_tokens = ["appimage", ".deb", ".rpm", "tar.gz", "zip"]

    candidates: list[tuple[int, str]] = []
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        url = str(asset.get("browser_download_url", "")).strip()
        if not url:
            continue
        score = 999
        for idx, token in enumerate(preferred_tokens):
            if token in name:
                score = idx
                break
        candidates.append((score, url))
    if not candidates:
        return ""
    candidates.sort(key=lambda row: row[0])
    return candidates[0][1]


def _select_release(owner: str, repo: str, include_prerelease: bool, timeout: int) -> dict:
    base = f"https://api.github.com/repos/{owner}/{repo}"
    if include_prerelease:
        releases = _fetch_json(f"{base}/releases", timeout=timeout)
        if not isinstance(releases, list):
            raise RuntimeError("Invalid releases response.")
        for release in releases:
            if isinstance(release, dict) and not release.get("draft"):
                return release
        raise RuntimeError("No releases found.")
    release = _fetch_json(f"{base}/releases/latest", timeout=timeout)
    if not isinstance(release, dict):
        raise RuntimeError("Invalid release response.")
    return release


def check_for_updates(
    current_version: str,
    owner: str,
    repo: str,
    include_prerelease: bool = False,
    timeout: int = 8,
) -> UpdateCheckResult:
    checked_at = datetime.now(timezone.utc).isoformat()
    owner = owner.strip()
    repo = repo.strip()
    if not owner or not repo:
        return UpdateCheckResult(
            success=False,
            has_update=False,
            message="Update repository owner/name is not configured.",
            current_version=current_version,
            checked_at=checked_at,
        )

    try:
        release = _select_release(owner, repo, include_prerelease, timeout)
    except RuntimeError as exc:
        return UpdateCheckResult(
            success=False,
            has_update=False,
            message=str(exc),
            current_version=current_version,
            checked_at=checked_at,
        )

    latest_raw = str(release.get("tag_name") or release.get("name") or "").strip()
    if not latest_raw:
        return UpdateCheckResult(
            success=False,
            has_update=False,
            message="Release does not include a valid version tag.",
            current_version=current_version,
            checked_at=checked_at,
        )

    try:
        has_update = is_newer_version(current_version, latest_raw)
    except ValueError as exc:
        return UpdateCheckResult(
            success=False,
            has_update=False,
            message=str(exc),
            current_version=current_version,
            checked_at=checked_at,
        )

    release_url = str(release.get("html_url", "")).strip()
    download_url = _asset_download_url(release)
    return UpdateCheckResult(
        success=True,
        has_update=has_update,
        message=(
            f"Update available: {latest_raw}" if has_update else f"You are up to date ({current_version})."
        ),
        current_version=current_version,
        latest_version=latest_raw,
        release_url=release_url,
        download_url=download_url,
        checked_at=checked_at,
    )

