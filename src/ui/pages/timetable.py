"""
Timetable page — Day / Week / Month calendar view.

Phase 1: Placeholder layout with view-switcher tabs and live unscheduled tasks.
"""
from datetime import datetime, timezone
from PyQt6.QtCore import QDate, Qt, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QCursor
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QSlider,
)
from sqlalchemy import or_

from src.database.models import Item, Scenario, SessionLocal, Tag
from src.ui.search_filters import parse_search_text


class DraggableTaskCard(QLabel):
    """A draggable unscheduled task card that can be moved to the calendar."""

    def __init__(self, text: str, item_id: int, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.item_id = item_id
        self.setWordWrap(True)
        self.setStyleSheet(
            "background-color: #2a2a3a; color: #d0d0e0; border-radius: 4px;"
            "padding: 8px; font-size: 12px; border: 1px solid #3a3a4e;"
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
        mime_data.setData("application/x-timetable-item", QByteArray.number(self.item_id))
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
        """Open item details (placeholder for now)."""
        # Import here to avoid circular import
        from src.ui.pages.todos import ItemDetailsDialog
        # Use a short-lived session only to load the item, then close it before showing the dialog.
        with SessionLocal() as session:
            item = session.query(Item).filter(Item.id == self.item_id).first()

        if not item:
            return

        dialog = ItemDetailsDialog(item, self)
        if dialog.exec():
            # Refresh the parent page
            timetable_page = self.find_timetable_page()
            if timetable_page:
                timetable_page.refresh_current()
    def find_timetable_page(self):
        """Find the TimetablePage parent widget."""
        widget = self.parent()
        while widget:
            if isinstance(widget, TimetablePage):
                return widget
            widget = widget.parent()
        return None


class ScalableCalendar(QCalendarWidget):
    """Calendar widget with drag & drop support and zoom capability."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._zoom_level = 1.0

    def dragEnterEvent(self, event):
        """Accept drag events with timetable item data."""
        if event.mimeData().hasFormat("application/x-timetable-item"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Accept drag move events."""
        if event.mimeData().hasFormat("application/x-timetable-item"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop - schedule item on the selected date."""
        if event.mimeData().hasFormat("application/x-timetable-item"):
            item_id_bytes = event.mimeData().data("application/x-timetable-item")
            item_id = int(item_id_bytes.data().decode())

            # Get the selected date
            selected_date = self.selectedDate()

            # Update the item's start time in the database
            with SessionLocal() as session:
                item = session.query(Item).filter(Item.id == item_id).first()
                if item:
                    # Set start_time to the selected date at current time
                    now = datetime.now(timezone.utc)
                    start_dt = datetime(
                        selected_date.year(),
                        selected_date.month(),
                        selected_date.day(),
                        now.hour,
                        now.minute,
                        tzinfo=timezone.utc
                    )
                    item.start_time = start_dt
                    session.commit()

            # Refresh the parent page
            timetable_page = self.find_timetable_page()
            if timetable_page:
                timetable_page.refresh_current()

            event.acceptProposedAction()

    def find_timetable_page(self):
        """Find the TimetablePage parent widget."""
        widget = self.parent()
        while widget:
            if isinstance(widget, TimetablePage):
                return widget
            widget = widget.parent()
        return None

    def set_zoom(self, zoom_level: float):
        """Set the zoom level for the calendar (affects font size)."""
        self._zoom_level = zoom_level
        font_size = int(12 * zoom_level)
        self.setStyleSheet(
            f"QCalendarWidget {{ background-color: #2a2a3a; color: #c8c8d8; font-size: {font_size}px; }}"
            f"QCalendarWidget QAbstractItemView {{ background-color: #2a2a3a; color: #c8c8d8;"
            f" selection-background-color: #5c85d6; font-size: {font_size}px; }}"
        )



class TimetablePage(QWidget):
    """Page 2 — Timetable calendar view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._unscheduled_layout: QVBoxLayout | None = None
        self._calendar: ScalableCalendar | None = None
        self._zoom_slider: QSlider | None = None
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

        # Add zoom controls
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        title_row.addWidget(zoom_label)

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setMinimum(50)
        self._zoom_slider.setMaximum(200)
        self._zoom_slider.setValue(100)
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.setStyleSheet(
            "QSlider::groove:horizontal { background: #2a2a3a; height: 4px; border-radius: 2px; }"
            "QSlider::handle:horizontal { background: #5c85d6; width: 12px; height: 12px;"
            " margin: -4px 0; border-radius: 6px; }"
        )
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        title_row.addWidget(self._zoom_slider)

        root.addLayout(title_row)

        # Splitter: calendar on the left, unscheduled sidebar on the right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._calendar = ScalableCalendar()
        self._calendar.setGridVisible(True)
        self._calendar.set_zoom(1.0)
        splitter.addWidget(self._calendar)

        sidebar = QWidget()
        sidebar.setMaximumWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 0, 0, 0)

        sidebar_title = QLabel("Unscheduled Tasks")
        sidebar_title.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold;")
        sidebar_layout.addWidget(sidebar_title)

        sidebar_info = QLabel("Drag tasks to the calendar to schedule them.")
        sidebar_info.setStyleSheet("color: #707080; font-size: 10px;")
        sidebar_info.setWordWrap(True)
        sidebar_layout.addWidget(sidebar_info)

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

    def _on_zoom_changed(self, value: int):
        """Handle zoom slider change."""
        if self._calendar:
            zoom_level = value / 100.0
            self._calendar.set_zoom(zoom_level)

    def refresh_items(self, scenario_name: str = "All", search_text: str = "") -> None:
        """Populate the unscheduled list with items that have no start time."""
        filters = parse_search_text(search_text)
        with SessionLocal() as session:
            query = session.query(Item).filter(Item.start_time.is_(None))
            if scenario_name != "All":
                query = query.join(Scenario).filter(Scenario.name == scenario_name)
            if filters.tags:
                query = query.filter(Item.tags.any(Tag.name.in_(filters.tags)))
            if filters.statuses:
                query = query.filter(Item.status.in_(filters.statuses))
            for term in filters.terms:
                like = f"%{term}%"
                query = query.filter(or_(Item.title.ilike(like), Item.description.ilike(like)))
            unscheduled = query.order_by(Item.created_at).all()

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
            card = DraggableTaskCard(text, item.id)
            self._unscheduled_layout.insertWidget(self._unscheduled_layout.count() - 1, card)

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

