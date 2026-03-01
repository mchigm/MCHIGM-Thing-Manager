"""
Timetable page — Day / Week / Month calendar view.

Phase 1: Placeholder layout with view-switcher tabs.
"""
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class TimetablePage(QWidget):
    """Page 2 — Timetable calendar view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Timetable — Calendar")
        title.setStyleSheet("color: #c8c8d8; font-size: 18px; font-weight: bold;")
        title_row.addWidget(title)
        title_row.addStretch()

        for label in ("Day", "Week", "Month"):
            btn = QPushButton(label)
            btn.setFixedWidth(64)
            btn.setStyleSheet(
                "QPushButton { background-color: #3a3a4a; color: #c0c0d0; border-radius: 4px;"
                " padding: 4px 8px; }"
                "QPushButton:hover { background-color: #4a4a5e; }"
            )
            title_row.addWidget(btn)

        root.addLayout(title_row)

        # Splitter: calendar on the left, unscheduled sidebar on the right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.setStyleSheet(
            "QCalendarWidget { background-color: #2a2a3a; color: #c8c8d8; }"
            "QCalendarWidget QAbstractItemView { background-color: #2a2a3a; color: #c8c8d8;"
            " selection-background-color: #5c85d6; }"
        )
        splitter.addWidget(calendar)

        # Unscheduled tasks sidebar
        sidebar = QWidget()
        sidebar.setMaximumWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 0, 0, 0)

        sidebar_title = QLabel("Unscheduled Tasks")
        sidebar_title.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold;")
        sidebar_layout.addWidget(sidebar_title)

        placeholder = QLabel("Drag tasks onto the calendar\nto schedule them.")
        placeholder.setStyleSheet("color: #606070; font-size: 11px;")
        placeholder.setWordWrap(True)
        sidebar_layout.addWidget(placeholder)
        sidebar_layout.addStretch()

        splitter.addWidget(sidebar)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)
