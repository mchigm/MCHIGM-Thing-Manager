"""
Plan page — Roadmap / Gantt view & Weekly Retrospective.

Phase 1: Placeholder layout (Gantt rendering via Qt Graphics View in Phase 5).
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PlanPage(QWidget):
    """Page 4 — Plan / Roadmap & Retrospective."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Plan — Roadmap & Retrospective")
        title.setStyleSheet("color: #c8c8d8; font-size: 18px; font-weight: bold;")
        title_row.addWidget(title)
        title_row.addStretch()

        retro_btn = QPushButton("Weekly Retrospective")
        retro_btn.setStyleSheet(
            "QPushButton { background-color: #5a4a7a; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; font-size: 12px; }"
            "QPushButton:hover { background-color: #6a5a8a; }"
        )
        retro_btn.clicked.connect(self._show_retro_placeholder)
        title_row.addWidget(retro_btn)
        root.addLayout(title_row)

        # Gantt placeholder using QGraphicsView
        self._scene = QGraphicsScene()
        self._scene.setBackgroundBrush(Qt.GlobalColor.darkGray)

        self._view = QGraphicsView(self._scene)
        self._view.setStyleSheet(
            "background-color: #1e1e2e; border-radius: 6px; border: 1px solid #3a3a4a;"
        )

        placeholder_text = self._scene.addText(
            "Gantt / Roadmap chart will render here in Phase 5.\n\n"
            "Items with dependencies will appear as linked bars."
        )
        placeholder_text.setDefaultTextColor(Qt.GlobalColor.lightGray)

        root.addWidget(self._view, stretch=1)

    def _show_retro_placeholder(self) -> None:
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Weekly Retrospective",
            "AI-generated retrospective will be available in Phase 5.\n\n"
            "It will summarize all items moved to Done this week and your Tracker data.",
        )
