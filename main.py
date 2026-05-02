"""
Entry point for MCHIGM Thing Manager.

Usage:
    python main.py
"""

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from src.database.models import ensure_seed_data
from src.i18n import tr
from src.ui.main_window import _APP_STYLE, MainWindow
from src.version import APP_VERSION

ensure_seed_data()
app = QApplication(sys.argv)
app.setApplicationName(tr("app.name", "MCHIGM Thing Manager"))
app.setApplicationVersion(APP_VERSION)
app.setStyleSheet(_APP_STYLE)
icon_path = Path(__file__).parent / "icon.png"
if icon_path.exists():
    app.setWindowIcon(QIcon(str(icon_path)))

window = MainWindow()
window.show()

sys.exit(app.exec())
