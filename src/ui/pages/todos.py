"""
TODOs page — Kanban board (Backlog → To-Do → Doing → Done).

Phase 1: Column structure with live items pulled from the database.
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
from sqlalchemy import or_

from src.database.models import Item, ItemStatus, Scenario, SessionLocal, Tag
from src.ui.search_filters import parse_search_text

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

    def set_cards(self, card_texts: list[str]) -> None:
        """Replace the column content with the provided cards."""
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not card_texts:
            self._add_card("No items yet.")
            return

        for text in card_texts:
            self._add_card(text)

    def _add_card(self, text: str) -> None:
        card = QLabel(text)
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
        self._columns: dict[ItemStatus, KanbanColumn] = {}
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
            self._columns[status] = col

        root.addLayout(columns_row)

    def refresh_items(self, scenario_name: str = "All", search_text: str = "") -> None:
        """Load items from the database and populate columns."""
        filters = parse_search_text(search_text)
        cards: dict[ItemStatus, list[str]] = {status: [] for status in ItemStatus}
        with SessionLocal() as session:
            query = session.query(Item)
            if scenario_name != "All":
                query = query.join(Scenario).filter(Scenario.name == scenario_name)
            if filters.tags:
                query = query.join(Item.tags).filter(Tag.name.in_(filters.tags))
            if filters.statuses:
                query = query.filter(Item.status.in_(filters.statuses))
            for term in filters.terms:
                like = f"%{term}%"
                query = query.filter(or_(Item.title.ilike(like), Item.description.ilike(like)))
            for item in query.order_by(Item.created_at).distinct().all():
                parts = [item.title, f"Type: {item.type.value}"]
                if item.deadline:
                    parts.append(f"Deadline: {item.deadline.strftime('%b %d, %H:%M')}")
                if item.tags:
                    tags = ", ".join(tag.name for tag in item.tags)
                    parts.append(f"Tags: {tags}")
                cards[item.status].append("\n".join(parts))

        for status, column in self._columns.items():
            column.set_cards(cards.get(status, []))
