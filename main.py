"""
Entry point for MCHIGM Thing Manager.

Usage:
    python main.py
"""
import sys

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow, _APP_STYLE


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("MCHIGM Thing Manager")
    app.setStyleSheet(_APP_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
