"""Unit tests for src/ui/feedback.py"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QWidget

from src.ui.feedback import find_main_window, show_app_message

_APP: QApplication | None = None


def _app() -> QApplication:
    global _APP
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    _APP = app
    return app


def test_find_main_window_returns_parent_window():
    _app()
    window = QMainWindow()
    window.setStatusBar(QStatusBar(window))
    child = QWidget(window)
    assert find_main_window(child) is window


def test_show_app_message_updates_status_bar():
    _app()
    window = QMainWindow()
    window.setStatusBar(QStatusBar(window))
    child = QWidget(window)
    assert show_app_message(child, "Saved item", 1000) is True
    assert window.statusBar().currentMessage() == "Saved item"
