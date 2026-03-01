"""
Timetable page — Day / Week / Month calendar view.

Phase 1: Placeholder layout with view-switcher tabs and live unscheduled tasks.
"""
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.database.models import Item, Scenario, SessionLocal


class TimetablePage(QWidget):
    """Page 2 — Timetable calendar view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._unscheduled_layout: QVBoxLayout | None = None
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

        sidebar = QWidget()
        sidebar.setMaximumWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 0, 0, 0)

        sidebar_title = QLabel("Unscheduled Tasks")
        sidebar_title.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold;")
        sidebar_layout.addWidget(sidebar_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        self._unscheduled_layout = QVBoxLayout(container)
        self._unscheduled_layout.setContentsMargins(0, 0, 0, 0)
        self._unscheduled_layout.setSpacing(8)
        self._unscheduled_layout.addStretch()

        scroll.setWidget(container)
        sidebar_layout.addWidget(scroll)
        splitter.addWidget(sidebar)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)

    def refresh_items(self, scenario_name: str = "All") -> None:
        """Populate the unscheduled list with items that have no start time."""
        with SessionLocal() as session:
            query = session.query(Item).filter(Item.start_time.is_(None)).order_by(Item.created_at)
            if scenario_name != "All":
                query = query.join(Scenario).filter(Scenario.name == scenario_name)
            unscheduled = query.all()

        if self._unscheduled_layout is None:
            return

        while self._unscheduled_layout.count() > 1:
            item = self._unscheduled_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not unscheduled:
            label = QLabel("Nothing unscheduled — drag new tasks here later.")
            label.setStyleSheet("color: #606070; font-size: 11px;")
            label.setWordWrap(True)
            self._unscheduled_layout.insertWidget(0, label)
            return

        for item in unscheduled:
            text = item.title
            if item.deadline:
                text += f"\nDeadline: {item.deadline.strftime('%b %d')}"
            label = QLabel(text)
            label.setStyleSheet(
                "background-color: #2a2a3a; color: #d0d0e0; border-radius: 4px;"
                "padding: 8px; font-size: 12px; border: 1px solid #3a3a4e;"
            )
            label.setWordWrap(True)
            self._unscheduled_layout.insertWidget(self._unscheduled_layout.count() - 1, label)
