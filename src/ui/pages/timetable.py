"""
Timetable page — Day / Week / Month calendar view.

Phase 1: Placeholder layout with view-switcher tabs and live unscheduled tasks.
"""
from datetime import datetime, timedelta, timezone
from PyQt6.QtCore import QDate, Qt, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QCursor, QTextCharFormat, QColor, QBrush
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QSlider,
    QButtonGroup,
)
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload

from src.database.models import Item, ItemType, Scenario, SessionLocal, Tag
from src.scheduling import occurrence_windows_for_item
from src.settings_store import load_settings
from src.ui.search_filters import parse_search_text


class DraggableTaskCard(QLabel):
    """A draggable unscheduled task card that can be moved to the calendar."""

    def __init__(self, text: str, item_id: int, scenario_color: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.item_id = item_id
        self.setWordWrap(True)
        left_border = f"3px solid {scenario_color}" if scenario_color else "none"
        self.setStyleSheet(
            f"background-color: #2a2a3a; color: #d0d0e0; border-radius: 4px;"
            f"padding: 8px; font-size: 12px; border: 1px solid #3a3a4e; border-left: {left_border};"
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

        with SessionLocal() as session:
            item = (
                session.query(Item)
                .options(selectinload(Item.tags), selectinload(Item.scenario))
                .filter(Item.id == self.item_id)
                .first()
            )
            if not item:
                return
            session.expunge(item)

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
    """Calendar widget with drag & drop support, zoom capability, and scheduled item highlighting."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._zoom_level = 1.0
        self._scheduled_dates: dict[QDate, list[tuple[str, str]]] = {}  # date -> [(title, color)]
        self._highlight_format = QTextCharFormat()
        self._highlight_format.setBackground(QBrush(QColor("#3a5a7a")))

    def set_scheduled_items(self, items_data: list[dict]) -> None:
        """Update the calendar with scheduled item indicators.
        
        Args:
            items_data: List of dicts with 'start_time', 'title', 'scenario_color' keys
        """
        self._scheduled_dates.clear()
        for data in items_data:
            start_time = data.get('start_time')
            if start_time:
                start_tz = start_time if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc)
                qdate = QDate(start_tz.year, start_tz.month, start_tz.day)
                color = data.get('scenario_color', "#5c85d6")
                if qdate not in self._scheduled_dates:
                    self._scheduled_dates[qdate] = []
                self._scheduled_dates[qdate].append((data['title'], color))
        self._update_date_formats()

    def _update_date_formats(self) -> None:
        """Apply visual formatting to dates with scheduled items."""
        # Reset all dates first
        default_format = QTextCharFormat()
        
        # Highlight dates with scheduled items
        for qdate, items in self._scheduled_dates.items():
            fmt = QTextCharFormat()
            # Use the color of the first item, or blend if multiple
            if items:
                color = QColor(items[0][1])
                color.setAlpha(100)
                fmt.setBackground(QBrush(color))
                fmt.setFontWeight(700)  # Bold
                # Add tooltip with item titles
                titles = [title for title, _ in items[:3]]
                if len(items) > 3:
                    titles.append(f"...and {len(items) - 3} more")
                fmt.setToolTip("\n".join(titles))
            self.setDateTextFormat(qdate, fmt)

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
            try:
                item_id_str = bytes(item_id_bytes).decode()
                item_id = int(item_id_str)
            except (ValueError, UnicodeDecodeError, TypeError):
                # Malformed or unexpected drag payload; ignore the drop.
                return

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
        self._view_buttons: list[QPushButton] = []
        self._current_view = "Month"
        self._scheduled_list_layout: QVBoxLayout | None = None
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

        # View switch buttons
        for label in ("Day", "Week", "Month"):
            btn = QPushButton(label)
            btn.setFixedWidth(64)
            btn.setCheckable(True)
            btn.setChecked(label == "Month")
            btn.clicked.connect(lambda checked, v=label: self._switch_view(v))
            self._view_buttons.append(btn)
            self._update_view_button_style(btn, label == "Month")
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

        # Left panel with calendar and scheduled items list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self._calendar = ScalableCalendar()
        self._calendar.setGridVisible(True)
        self._calendar.set_zoom(1.0)
        self._calendar.selectionChanged.connect(self._on_date_selected)
        left_layout.addWidget(self._calendar)

        # Scheduled items for selected date
        scheduled_header = QHBoxLayout()
        scheduled_label = QLabel("Scheduled for selected date:")
        scheduled_label.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")
        scheduled_header.addWidget(scheduled_label)
        scheduled_header.addStretch()
        
        # Add item button for selected date
        add_scheduled_btn = QPushButton("+")
        add_scheduled_btn.setFixedSize(24, 24)
        add_scheduled_btn.setStyleSheet(
            "QPushButton { background-color: #5cd685; color: #1a1a2e; border-radius: 12px;"
            " font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #6ce695; }"
        )
        add_scheduled_btn.setToolTip("Create new item for selected date")
        add_scheduled_btn.clicked.connect(self._create_item_for_date)
        scheduled_header.addWidget(add_scheduled_btn)
        
        left_layout.addLayout(scheduled_header)

        scheduled_scroll = QScrollArea()
        scheduled_scroll.setWidgetResizable(True)
        scheduled_scroll.setMaximumHeight(120)
        scheduled_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        scheduled_container = QWidget()
        self._scheduled_list_layout = QVBoxLayout(scheduled_container)
        self._scheduled_list_layout.setContentsMargins(0, 0, 0, 0)
        self._scheduled_list_layout.setSpacing(4)
        self._scheduled_list_layout.addStretch()

        scheduled_scroll.setWidget(scheduled_container)
        left_layout.addWidget(scheduled_scroll)

        splitter.addWidget(left_panel)

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
        
        # Statistics section
        stats_frame = QFrame()
        stats_frame.setStyleSheet(
            "QFrame { background-color: #2a2a3a; border-radius: 6px; padding: 4px; }"
        )
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(8, 8, 8, 8)
        stats_layout.setSpacing(4)
        
        stats_title = QLabel("📊 Statistics")
        stats_title.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(stats_title)
        
        # Stats labels
        self._stats_labels = {}
        stat_items = [
            ("today", "Today:"),
            ("this_week", "This Week:"),
            ("this_month", "This Month:"),
            ("today_workload", "Today Workload:"),
            ("avg_time_week", "Avg Time/Week:"),
        ]
        for key, label_text in stat_items:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setStyleSheet("color: #808090; font-size: 10px;")
            row.addWidget(label)
            value_label = QLabel("0")
            value_label.setStyleSheet("color: #c8c8d8; font-size: 10px; font-weight: bold;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(value_label)
            stats_layout.addLayout(row)
            self._stats_labels[key] = value_label
        
        sidebar_layout.addWidget(stats_frame)
        
        splitter.addWidget(sidebar)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)

    def _update_view_button_style(self, btn: QPushButton, active: bool) -> None:
        """Update the style of a view button."""
        if active:
            btn.setStyleSheet(
                "QPushButton { background-color: #5c85d6; color: #ffffff; border-radius: 4px;"
                " padding: 4px 8px; font-weight: bold; }"
                "QPushButton:hover { background-color: #6a95e6; }"
            )
        else:
            btn.setStyleSheet(
                "QPushButton { background-color: #3a3a4a; color: #c0c0d0; border-radius: 4px;"
                " padding: 4px 8px; }"
                "QPushButton:hover { background-color: #4a4a5e; }"
            )

    def _switch_view(self, view: str) -> None:
        """Switch between Day, Week, and Month views."""
        self._current_view = view
        for btn in self._view_buttons:
            is_active = btn.text() == view
            btn.setChecked(is_active)
            self._update_view_button_style(btn, is_active)

        if self._calendar:
            if view == "Day":
                # Show single day - navigate to selected date and set 1 row
                self._calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
            elif view == "Week":
                # Show week view
                self._calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.ISOWeekNumbers)
            else:  # Month
                self._calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.ISOWeekNumbers)

    def _on_date_selected(self) -> None:
        """Update the scheduled items list when a date is selected."""
        if not self._calendar or not self._scheduled_list_layout:
            return

        selected = self._calendar.selectedDate()
        self._update_scheduled_list(selected)

    def _create_item_for_date(self) -> None:
        """Create a new item scheduled for the selected date."""
        if not self._calendar:
            return
        
        from src.ui.pages.todos import NewItemDialog
        from src.database.models import ItemStatus, ItemType
        
        selected = self._calendar.selectedDate()
        # Pre-fill with the selected date at 9:00 AM
        template_data = {
            'type': ItemType.EVENT,
            'start_date': selected,
        }
        
        dialog = NewItemDialog(ItemStatus.TODO, self, template_data)
        dialog.setWindowTitle(f"New Item for {selected.toString('MMM dd, yyyy')}")
        
        if dialog.exec():
            # Update the item with the selected date/time
            # The dialog creates the item, but we need to set the start_time
            # For now, refresh the view
            self.refresh_current()

    def _update_scheduled_list(self, qdate: QDate) -> None:
        """Show items scheduled for the selected date."""
        if not self._scheduled_list_layout:
            return

        # Clear existing items
        while self._scheduled_list_layout.count() > 1:
            item = self._scheduled_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Query items for this date
        start_of_day = datetime(qdate.year(), qdate.month(), qdate.day(), 0, 0, 0, tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)
        buffer_per_hour = load_settings().get("buffer_time_per_hour", 45)
        occurrences: list[tuple[datetime, Item]] = []

        with SessionLocal() as session:
            items = (
                session.query(Item)
                .options(joinedload(Item.scenario))
                .filter(Item.start_time.isnot(None))
                .all()
            )
            for item in items:
                windows = occurrence_windows_for_item(
                    item,
                    buffer_per_hour=buffer_per_hour,
                    window_start=start_of_day,
                    window_end=end_of_day,
                )
                for start, _ in windows:
                    occurrences.append((start, item))

        if not occurrences:
            label = QLabel("No items scheduled for this date.")
            label.setStyleSheet("color: #606070; font-size: 11px;")
            self._scheduled_list_layout.insertWidget(0, label)
            return

        for start, item in sorted(occurrences, key=lambda row: row[0]):
            time_str = start.strftime("%H:%M")
            color = item.scenario.color if item.scenario else "#5c85d6"
            type_icon = {"Task": "📋", "Event": "📅", "Note": "📝", "Goal": "🎯"}.get(item.type.value, "📋")
            label = QLabel(f"{type_icon} {time_str} {item.title}")
            label.setStyleSheet(
                f"color: #c8c8d8; font-size: 11px; padding: 4px; "
                f"background-color: #2a2a3a; border-left: 3px solid {color}; border-radius: 2px;"
            )
            label.setWordWrap(True)
            self._scheduled_list_layout.insertWidget(self._scheduled_list_layout.count() - 1, label)

    def _on_zoom_changed(self, value: int):
        """Handle zoom slider change."""
        if self._calendar:
            zoom_level = value / 100.0
            self._calendar.set_zoom(zoom_level)

    def refresh_items(self, scenario_name: str = "All", search_text: str = "") -> None:
        """Populate the unscheduled list and highlight scheduled dates."""
        filters = parse_search_text(search_text)
        
        # Store extracted data from items within session
        unscheduled_data = []
        scheduled_data = []
        
        with SessionLocal() as session:
            # Get unscheduled items - eagerly load scenario
            unscheduled_query = session.query(Item).options(joinedload(Item.scenario)).filter(Item.start_time.is_(None))
            if scenario_name != "All":
                unscheduled_query = unscheduled_query.join(Scenario).filter(Scenario.name == scenario_name)
            if filters.tags:
                unscheduled_query = unscheduled_query.filter(Item.tags.any(Tag.name.in_(filters.tags)))
            if filters.statuses:
                unscheduled_query = unscheduled_query.filter(Item.status.in_(filters.statuses))
            for term in filters.terms:
                like = f"%{term}%"
                unscheduled_query = unscheduled_query.filter(or_(Item.title.ilike(like), Item.description.ilike(like)))
            unscheduled = unscheduled_query.order_by(Item.created_at).all()
            
            # Extract data while in session
            for item in unscheduled:
                unscheduled_data.append({
                    'id': item.id,
                    'title': item.title,
                    'type_value': item.type.value,
                    'deadline': item.deadline,
                    'scenario_color': item.scenario.color if item.scenario else None,
                })

            # Get scheduled items for calendar highlighting (including repeating schedules)
            scheduled_query = session.query(Item).options(joinedload(Item.scenario)).filter(Item.start_time.isnot(None))
            if scenario_name != "All":
                scheduled_query = scheduled_query.outerjoin(Scenario).filter(Scenario.name == scenario_name)
            if filters.tags:
                scheduled_query = scheduled_query.filter(Item.tags.any(Tag.name.in_(filters.tags)))
            if filters.statuses:
                scheduled_query = scheduled_query.filter(Item.status.in_(filters.statuses))
            for term in filters.terms:
                like = f"%{term}%"
                scheduled_query = scheduled_query.filter(or_(Item.title.ilike(like), Item.description.ilike(like)))
            scheduled = scheduled_query.all()

            # Extract scheduled data while in session
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(days=30)
            window_end = now + timedelta(days=365)
            buffer_per_hour = load_settings().get("buffer_time_per_hour", 45)
            for item in scheduled:
                windows = occurrence_windows_for_item(
                    item,
                    buffer_per_hour=buffer_per_hour,
                    window_start=window_start,
                    window_end=window_end,
                )
                for start, _ in windows:
                    scheduled_data.append({
                        'id': item.id,
                        'title': item.title,
                        'start_time': start,
                        'type_value': item.type.value,
                        'scenario_color': item.scenario.color if item.scenario else "#5c85d6",
                    })

            # Update calendar with scheduled items (pass extracted data)
            if self._calendar:
                self._calendar.set_scheduled_items(scheduled_data)

        if self._unscheduled_layout is None:
            return

        while self._unscheduled_layout.count() > 1:
            item = self._unscheduled_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not unscheduled_data:
            label = QLabel("Nothing unscheduled — drag new tasks here later.")
            label.setStyleSheet("color: #606070; font-size: 11px;")
            label.setWordWrap(True)
            self._unscheduled_layout.insertWidget(0, label)
        else:
            for data in unscheduled_data:
                # Add type icon and scenario color
                type_icon = {"Task": "📋", "Event": "📅", "Note": "📝", "Goal": "🎯"}.get(data['type_value'], "📋")
                text = f"{type_icon} {data['title']}"
                if data['deadline']:
                    text += f"\nDeadline: {data['deadline'].strftime('%b %d')}"
                card = DraggableTaskCard(text, data['id'], data['scenario_color'])
                self._unscheduled_layout.insertWidget(self._unscheduled_layout.count() - 1, card)

        # Update scheduled list for current date
        if self._calendar:
            self._update_scheduled_list(self._calendar.selectedDate())
        
        # Update statistics
        self._update_stats()

    def _update_stats(self) -> None:
        """Update the statistics display."""
        if not hasattr(self, '_stats_labels') or not self._stats_labels:
            return

        with SessionLocal() as session:
            today = datetime.now(timezone.utc).date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=7)
            month_start = today.replace(day=1)
            if today.month == 12:
                month_end = today.replace(year=today.year + 1, month=1, day=1)
            else:
                month_end = today.replace(month=today.month + 1, day=1)

            today_start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc)
            today_end = today_start + timedelta(days=1)
            week_start_dt = datetime(week_start.year, week_start.month, week_start.day, 0, 0, 0, tzinfo=timezone.utc)
            week_end_dt = datetime(week_end.year, week_end.month, week_end.day, 0, 0, 0, tzinfo=timezone.utc)
            month_start_dt = datetime(month_start.year, month_start.month, month_start.day, 0, 0, 0, tzinfo=timezone.utc)
            month_end_dt = datetime(month_end.year, month_end.month, month_end.day, 0, 0, 0, tzinfo=timezone.utc)

            items = session.query(Item).filter(Item.start_time.isnot(None)).all()
            buffer_per_hour = load_settings().get("buffer_time_per_hour", 45)
            windows: list[tuple[datetime, Item]] = []
            for item in items:
                for start, _ in occurrence_windows_for_item(
                    item,
                    buffer_per_hour=buffer_per_hour,
                    window_start=week_start_dt,
                    window_end=month_end_dt,
                ):
                    windows.append((start, item))

            today_count = sum(1 for start, _ in windows if today_start <= start < today_end)
            week_count = sum(1 for start, _ in windows if week_start_dt <= start < week_end_dt)
            month_count = sum(1 for start, _ in windows if month_start_dt <= start < month_end_dt)

            today_workload = sum(
                (item.workload or 0)
                for start, item in windows
                if today_start <= start < today_end
            )

            week_time = sum(
                (item.estimated_time or 0)
                for start, item in windows
                if week_start_dt <= start < week_end_dt
            )
            avg_time_display = f"{week_time} min" if week_time > 0 else "0 min"
        
        # Update labels
        self._stats_labels['today'].setText(f"{today_count} items")
        self._stats_labels['this_week'].setText(f"{week_count} items")
        self._stats_labels['this_month'].setText(f"{month_count} items")
        self._stats_labels['today_workload'].setText(f"Level {today_workload}" if today_workload > 0 else "None")
        self._stats_labels['avg_time_week'].setText(avg_time_display)

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
