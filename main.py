"""
Entry point for MCHIGM Thing Manager.

Usage:
    python main.py
"""
import sys

from PyQt6.QtWidgets import QApplication

from src.database.models import ensure_seed_data
from src.ui.main_window import MainWindow, _APP_STYLE


def main() -> None:
    ensure_seed_data()
    app = QApplication(sys.argv)
    app.setApplicationName("MCHIGM Thing Manager")
    app.setStyleSheet(_APP_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
