"""Shared, non-modal UI feedback helpers."""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget


def find_main_window(widget: QWidget | None) -> QMainWindow | None:
    current = widget
    while current is not None:
        if isinstance(current, QMainWindow):
            return current
        current = current.parentWidget()
    app = QApplication.instance()
    if app and isinstance(app.activeWindow(), QMainWindow):
        return app.activeWindow()
    return None


def show_app_message(widget: QWidget | None, message: str, timeout_ms: int = 2500) -> bool:
    window = find_main_window(widget)
    if not window:
        return False
    status_bar = window.statusBar()
    if not status_bar:
        return False
    status_bar.showMessage(message, timeout_ms)
    return True
