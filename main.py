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
from src.version import APP_VERSION
from src.ui.main_window import MainWindow, _APP_STYLE


def main() -> None:
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


if __name__ == "__main__":
    main()
