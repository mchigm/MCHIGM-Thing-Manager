"""
Background worker for update checks to keep UI responsive.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from src.updater import UpdateCheckResult, check_for_updates


class UpdateCheckWorker(QObject):
    """Run update checks off the UI thread."""

    finished = pyqtSignal(object)

    def __init__(
        self,
        current_version: str,
        owner: str,
        repo: str,
        include_prerelease: bool,
    ) -> None:
        super().__init__()
        self._current_version = current_version
        self._owner = owner
        self._repo = repo
        self._include_prerelease = include_prerelease

    def run(self) -> None:
        result: UpdateCheckResult = check_for_updates(
            current_version=self._current_version,
            owner=self._owner,
            repo=self._repo,
            include_prerelease=self._include_prerelease,
        )
        self.finished.emit(result)

