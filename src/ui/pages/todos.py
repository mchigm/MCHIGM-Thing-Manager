"""
TODOs page — Kanban board (Backlog → To-Do → Doing → Done).

Phase 1: Column structure with live items pulled from the database.
"""
from PyQt6.QtCore import Qt, QTimer, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QCursor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QDialog,
    QTextEdit,
    QLineEdit,
    QFormLayout,
    QDialogButtonBox,
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


class DraggableCard(QLabel):
    """A draggable Kanban card that stores its item ID and supports drag & drop."""

    def __init__(self, text: str, item_id: int, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.item_id = item_id
        self.setWordWrap(True)
        self.setStyleSheet(
            "background-color: #3c3c50; color: #e0e0e0; border-radius: 4px;"
            "padding: 8px; font-size: 12px;"
        )
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, event):
        """Handle mouse press - start drag or open details on click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move - initiate drag operation."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return

        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-kanban-item", QByteArray.number(self.item_id))
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, event):
        """Handle mouse release - open details if not dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            if (event.pos() - self.drag_start_position).manhattanLength() < 10:
                # It was a click, not a drag - open details
                self.show_details()
        super().mouseReleaseEvent(event)

    def show_details(self):
        """Open item details dialog."""
        with SessionLocal() as session:
            item = session.query(Item).filter(Item.id == self.item_id).first()
            if not item:
                return
            # Detach the item from the session so the session can be closed
            # before the dialog is shown, avoiding a long-lived DB session
            session.expunge(item)

        # Create and execute the dialog outside of the DB session context
        dialog = ItemDetailsDialog(item, self)
        if dialog.exec():
            # Refresh the parent page if changes were made
            todos_page = self.find_todos_page()
            if todos_page:
                todos_page.refresh_current()

    def find_todos_page(self):
        """Find the TodosPage parent widget."""
        widget = self.parent()
        while widget:
            if isinstance(widget, TodosPage):
                return widget
            widget = widget.parent()
        return None


class ItemDetailsDialog(QDialog):
    """Dialog for viewing and editing item details."""

    def __init__(self, item: Item, parent: QWidget | None = None):
        super().__init__(parent)
        self.item_id = item.id
        self.setWindowTitle(f"Item Details - {item.title}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._setup_ui(item)

    def _setup_ui(self, item: Item):
        layout = QVBoxLayout(self)

        # Form for editing
        form = QFormLayout()

        self.title_edit = QLineEdit(item.title)
        self.title_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 4px;"
        )
        form.addRow("Title:", self.title_edit)

        self.description_edit = QTextEdit(item.description or "")
        self.description_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 4px;"
        )
        self.description_edit.setMinimumHeight(150)
        form.addRow("Description:", self.description_edit)

        # Read-only info
        info_text = f"""
        Type: {item.type.value}
        Status: {item.status.value}
        Scenario: {item.scenario.name if item.scenario else 'None'}
        Tags: {', '.join(tag.name for tag in item.tags) if item.tags else 'None'}
        Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}
        """
        if item.deadline:
            info_text += f"\nDeadline: {item.deadline.strftime('%Y-%m-%d %H:%M')}"
        if item.start_time:
            info_text += f"\nStart: {item.start_time.strftime('%Y-%m-%d %H:%M')}"
        if item.end_time:
            info_text += f"\nEnd: {item.end_time.strftime('%Y-%m-%d %H:%M')}"

        info_label = QLabel(info_text.strip())
        info_label.setStyleSheet("color: #a0a0b0; font-size: 11px; padding: 8px;")
        info_label.setWordWrap(True)
        form.addRow("Info:", info_label)

        layout.addLayout(form)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def save_changes(self):
        """Save changes to the database."""
        with SessionLocal() as session:
            item = session.query(Item).filter(Item.id == self.item_id).first()
            if item:
                item.title = self.title_edit.text().strip()[:255]
                item.description = self.description_edit.toPlainText().strip()
                session.commit()
        self.accept()


class KanbanColumn(QWidget):
    """A single Kanban column with a header and a scrollable card area."""

    def __init__(self, status: ItemStatus, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status = status
        self.setAcceptDrops(True)
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

    def dragEnterEvent(self, event):
        """Accept drag events with kanban item data."""
        if event.mimeData().hasFormat("application/x-kanban-item"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Accept drag move events."""
        if event.mimeData().hasFormat("application/x-kanban-item"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop - update item status in database."""
        if event.mimeData().hasFormat("application/x-kanban-item"):
            item_id_bytes = event.mimeData().data("application/x-kanban-item")
            try:
                item_id_str = bytes(item_id_bytes).decode()
                item_id = int(item_id_str)
            except ValueError:
                # Malformed drag payload; ignore the drop to avoid crashing
                return

            # Update the item's status in the database
            with SessionLocal() as session:
                item = session.query(Item).filter(Item.id == item_id).first()
                if item:
                    item.status = self._status
                    session.commit()

            # Refresh the parent page
            todos_page = self.find_todos_page()
            if todos_page:
                todos_page.refresh_current()

            event.acceptProposedAction()

    def find_todos_page(self):
        """Find the TodosPage parent widget."""
        widget = self.parent()
        while widget:
            if isinstance(widget, TodosPage):
                return widget
            widget = widget.parent()
        return None

    def set_cards(self, cards_data: list[tuple[str, int]]) -> None:
        """Replace the column content with the provided cards (text, item_id tuples)."""
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not cards_data:
            self._add_placeholder()
            return

        for text, item_id in cards_data:
            self._add_card(text, item_id)

    def _add_card(self, text: str, item_id: int) -> None:
        """Add a draggable card to the column."""
        card = DraggableCard(text, item_id)
        # Insert before the trailing stretch
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    def _add_placeholder(self) -> None:
        """Add a placeholder label when column is empty."""
        label = QLabel("No items yet.")
        label.setWordWrap(True)
        label.setStyleSheet(
            "background-color: #3c3c50; color: #e0e0e0; border-radius: 4px;"
            "padding: 8px; font-size: 12px;"
        )
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, label)


class TodosPage(QWidget):
    """Page 1 — TODO Kanban board."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._columns: dict[ItemStatus, KanbanColumn] = {}
        self._tracker_timer = QTimer(self)
        self._tracker_timer.timeout.connect(self._tick_tracker)
        self._tracking = False
        self._elapsed_seconds = 0
        self._tracker_frame: QWidget | None = None
        self._tracker_label: QLabel | None = None
        self._tracker_button: QPushButton | None = None
        self._setup_ui()


    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("TODOs — Action Hub")
        title.setStyleSheet("color: #c8c8d8; font-size: 18px; font-weight: bold;")
        root.addWidget(title)

        tracker = self._build_tracker()
        root.addWidget(tracker)

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
        cards: dict[ItemStatus, list[tuple[str, int]]] = {status: [] for status in ItemStatus}
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
                cards[item.status].append(("\n".join(parts), item.id))

        for status, column in self._columns.items():
            column.set_cards(cards.get(status, []))
        self._update_tracker_visibility(bool(cards.get(ItemStatus.DOING)))

    def refresh_current(self) -> None:
        """Refresh with current scenario and search settings from parent window."""
        # Find main window to get current scenario and search
        main_window = self.window()
        if hasattr(main_window, '_scenario_combo') and hasattr(main_window, '_search_bar'):
            scenario = main_window._scenario_combo.currentText()
            search = main_window._search_bar.text()
            self.refresh_items(scenario, search)
        else:
            self.refresh_items()

    # ------------------------------------------------------------------
    # Time tracker
    # ------------------------------------------------------------------
    def _build_tracker(self) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: #232336; border: 1px solid #3a3a4e; border-radius: 6px;"
            "padding: 8px;"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        label = QLabel("Tracker is available while there are cards in Doing.")
        label.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        layout.addWidget(label)

        self._tracker_label = QLabel("00:00:00")
        self._tracker_label.setStyleSheet("color: #c8c8d8; font-family: monospace;")
        layout.addWidget(self._tracker_label)

        self._tracker_button = QPushButton("Start")
        self._tracker_button.setFixedWidth(70)
        self._tracker_button.setStyleSheet(
            "QPushButton { background-color: #5c85d6; color: #ffffff; border-radius: 4px; "
            "padding: 4px 8px; } QPushButton:hover { background-color: #6a95e6; }"
        )
        self._tracker_button.clicked.connect(self._toggle_tracker)
        layout.addWidget(self._tracker_button)

        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(70)
        reset_btn.setStyleSheet(
            "QPushButton { background-color: #3a3a4e; color: #c8c8d8; border-radius: 4px; "
            "padding: 4px 8px; } QPushButton:hover { background-color: #4a4a6e; }"
        )
        reset_btn.clicked.connect(self._reset_tracker)
        layout.addWidget(reset_btn)

        layout.addStretch()
        self._tracker_frame = frame
        frame.hide()
        return frame

    def _toggle_tracker(self) -> None:
        if not self._tracker_button:
            return
        self._tracking = not self._tracking
        if self._tracking:
            self._tracker_timer.start(1000)
            self._tracker_button.setText("Pause")
        else:
            self._tracker_timer.stop()
            self._tracker_button.setText("Start")

    def _reset_tracker(self) -> None:
        self._tracker_timer.stop()
        self._tracking = False
        self._elapsed_seconds = 0
        if self._tracker_button:
            self._tracker_button.setText("Start")
        self._update_tracker_label()

    def _tick_tracker(self) -> None:
        if not self._tracking:
            return
        self._elapsed_seconds += 1
        self._update_tracker_label()

    def _update_tracker_label(self) -> None:
        if not self._tracker_label:
            return
        hours, remainder = divmod(self._elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self._tracker_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")

    def _update_tracker_visibility(self, has_doing: bool) -> None:
        if not self._tracker_frame:
            return
        if has_doing:
            self._tracker_frame.show()
        else:
            self._reset_tracker()
            self._tracker_frame.hide()
