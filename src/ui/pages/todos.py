"""
TODOs page — Kanban board (Backlog → To-Do → Doing → Done).

Phase 1: Column structure with placeholder cards.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.database.models import ItemStatus

_COLUMN_COLORS = {
    ItemStatus.BACKLOG: "#4a4a5a",
    ItemStatus.TODO:    "#3a5a7a",
    ItemStatus.DOING:   "#5a4a7a",
    ItemStatus.DONE:    "#3a6a4a",
}


class KanbanColumn(QWidget):
    """A single Kanban column with a header and a scrollable card area."""

    def __init__(self, status: ItemStatus, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status = status
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QLabel(self._status.value)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(40)
        color = _COLUMN_COLORS.get(self._status, "#4a4a4a")
        header.setStyleSheet(
            f"background-color: {color}; color: #ffffff; font-weight: bold; font-size: 13px;"
            " border-top-left-radius: 6px; border-top-right-radius: 6px; padding: 4px;"
        )
        root.addWidget(header)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #2e2e3e;")

        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background-color: #2e2e3e;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(8, 8, 8, 8)
        self._cards_layout.setSpacing(6)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_widget)
        root.addWidget(scroll)

    def add_placeholder(self, title: str) -> None:
        """Add a placeholder card to the column (for Phase 1 demo)."""
        card = QLabel(title)
        card.setWordWrap(True)
        card.setStyleSheet(
            "background-color: #3c3c50; color: #e0e0e0; border-radius: 4px;"
            "padding: 8px; font-size: 12px;"
        )
        # Insert before the trailing stretch
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)


class TodosPage(QWidget):
    """Page 1 — TODO Kanban board."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("TODOs — Action Hub")
        title.setStyleSheet("color: #c8c8d8; font-size: 18px; font-weight: bold;")
        root.addWidget(title)

        columns_row = QHBoxLayout()
        columns_row.setSpacing(8)

        for status in (ItemStatus.BACKLOG, ItemStatus.TODO, ItemStatus.DOING, ItemStatus.DONE):
            col = KanbanColumn(status)
            columns_row.addWidget(col)

        root.addLayout(columns_row)
