"""
TODOs page — Kanban board (Backlog → To-Do → Doing → Done).

Phase 1: Column structure with live items pulled from the database.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from PyQt6.QtCore import Qt, QTimer, QMimeData, QByteArray, QDateTime, QUrl
from PyQt6.QtGui import QDrag, QCursor, QDesktopServices
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QDialog,
    QTextEdit,
    QLineEdit,
    QFormLayout,
    QDialogButtonBox,
    QComboBox,
    QCheckBox,
    QDateTimeEdit,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from src.database.models import Item, ItemStatus, ItemType, ItemTemplate, Scenario, SessionLocal, Tag
from src.scheduling import calculate_buffer_minutes
from src.ui.search_filters import parse_search_text
from src.settings_store import load_settings

_COLUMN_COLORS = {
    ItemStatus.BACKLOG: "#4a4a5a",
    ItemStatus.TODO:    "#3a5a7a",
    ItemStatus.DOING:   "#5a4a7a",
    ItemStatus.DONE:    "#3a6a4a",
}
_LEVEL_PREFIX = "!level:"


def _load_emergency_levels() -> list[dict[str, str]]:
    settings = load_settings()
    levels = settings.get("emergency_levels") or []
    fallback = [
        {"name": "Low", "color": "#5c85d6"},
        {"name": "Medium", "color": "#d6b55c"},
        {"name": "High", "color": "#d65c5c"},
    ]
    cleaned = []
    for level in levels:
        name = (level or {}).get("name", "").strip()
        color = (level or {}).get("color", "").strip() or "#d65c5c"
        if name:
            cleaned.append({"name": name, "color": color})
    return cleaned or fallback


def _level_from_tags(tags: list[Tag]) -> str | None:
    for tag in tags:
        if tag.name.startswith(_LEVEL_PREFIX):
            return tag.name[len(_LEVEL_PREFIX):]
    return None


def _level_color(level_name: str | None, levels: list[dict[str, str]]) -> str | None:
    if not level_name:
        return None
    for level in levels:
        if level.get("name") == level_name:
            return level.get("color")
    return None


class DraggableCard(QLabel):
    """A draggable Kanban card that stores its item ID and supports drag & drop."""

    # Class-level set to track selected cards
    _selected_items: set[int] = set()

    def __init__(self, text: str, item_id: int, accent_color: str | None = None, deadline_status: str | None = None, scenario_color: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.item_id = item_id
        self._is_selected = False
        self._accent_color = accent_color
        self._deadline_status = deadline_status
        self._scenario_color = scenario_color
        self.setWordWrap(True)
        self._update_style()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _update_style(self):
        """Update card style based on selection state."""
        # Determine border based on deadline status
        if self._is_selected:
            border = "2px solid #5cd685"  # Green for selected
            bg = "#4a4a60"
        elif self._deadline_status == "overdue":
            border = "2px solid #d65c5c"
            bg = "#3c3c50"
        elif self._deadline_status == "urgent":
            border = "2px solid #d6a55c"
            bg = "#3c3c50"
        elif self._accent_color:
            border = f"2px solid {self._accent_color}"
            bg = "#3c3c50"
        else:
            border = "none"
            bg = "#3c3c50"
        
        left_border = f"3px solid {self._scenario_color}" if self._scenario_color else "none"
        
        self.setStyleSheet(
            f"background-color: {bg}; color: #e0e0e0; border-radius: 4px;"
            f"padding: 8px; font-size: 12px; border: {border}; border-left: {left_border};"
        )

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
        """Handle mouse release - open details if not dragging, or toggle selection with Ctrl."""
        if event.button() == Qt.MouseButton.LeftButton:
            if (event.pos() - self.drag_start_position).manhattanLength() < 10:
                # Check for Ctrl modifier for multi-select
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self._toggle_selection()
                else:
                    # Clear other selections and open details
                    DraggableCard._selected_items.clear()
                    self._clear_all_selections()
                    self.show_details()
        super().mouseReleaseEvent(event)

    def _toggle_selection(self):
        """Toggle selection state of this card."""
        self._is_selected = not self._is_selected
        if self._is_selected:
            DraggableCard._selected_items.add(self.item_id)
        else:
            DraggableCard._selected_items.discard(self.item_id)
        self._update_style()
        
        # Show batch edit button if multiple selected
        todos_page = self.find_todos_page()
        if todos_page:
            todos_page._update_batch_edit_button()

    def _clear_all_selections(self):
        """Clear selection style from all cards."""
        todos_page = self.find_todos_page()
        if todos_page:
            todos_page._clear_all_card_selections()

    def show_details(self):
        """Open item details dialog."""
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
        self._levels = _load_emergency_levels()
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

        # Emergency level
        self.level_combo = QComboBox()
        self.level_combo.addItem("None")
        current_level = _level_from_tags(item.tags)
        for level in self._levels:
            self.level_combo.addItem(level["name"])
        if current_level:
            idx = self.level_combo.findText(current_level)
            if idx >= 0:
                self.level_combo.setCurrentIndex(idx)
        form.addRow("Emergency:", self.level_combo)

        # Start time
        self.start_time_enabled = QCheckBox("Set start time")
        self.start_time_enabled.setChecked(bool(item.start_time))
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setCalendarPopup(True)
        start_dt = item.start_time or datetime.now(timezone.utc)
        self.start_time_edit.setDateTime(
            QDateTime(
                start_dt.year,
                start_dt.month,
                start_dt.day,
                start_dt.hour,
                start_dt.minute,
            )
        )
        self.start_time_edit.setEnabled(self.start_time_enabled.isChecked())
        self.start_time_enabled.toggled.connect(self.start_time_edit.setEnabled)
        start_row = QHBoxLayout()
        start_row.addWidget(self.start_time_enabled)
        start_row.addWidget(self.start_time_edit)
        form.addRow("Start:", start_row)

        # Deadline
        self.deadline_enabled = QCheckBox("Set deadline")
        self.deadline_enabled.setChecked(bool(item.deadline))
        self.deadline_edit = QDateTimeEdit()
        self.deadline_edit.setCalendarPopup(True)
        deadline_dt = item.deadline or datetime.now(timezone.utc)
        self.deadline_edit.setDateTime(
            QDateTime(
                deadline_dt.year,
                deadline_dt.month,
                deadline_dt.day,
                deadline_dt.hour,
                deadline_dt.minute,
            )
        )
        self.deadline_edit.setEnabled(self.deadline_enabled.isChecked())
        self.deadline_enabled.toggled.connect(self.deadline_edit.setEnabled)
        deadline_row = QHBoxLayout()
        deadline_row.addWidget(self.deadline_enabled)
        deadline_row.addWidget(self.deadline_edit)
        form.addRow("Deadline:", deadline_row)

        # Repeat schedule
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItem("None", None)
        self.repeat_combo.addItem("Daily", "daily")
        self.repeat_combo.addItem("Weekly", "weekly")
        self.repeat_combo.addItem("Monthly", "monthly")
        repeat_pattern = (item.repeat_pattern or "").strip().lower()
        for idx in range(self.repeat_combo.count()):
            if (self.repeat_combo.itemData(idx) or "") == repeat_pattern:
                self.repeat_combo.setCurrentIndex(idx)
                break
        form.addRow("Repeat:", self.repeat_combo)

        self.repeat_until_enabled = QCheckBox("Set repeat end")
        self.repeat_until_enabled.setChecked(bool(item.repeat_until))
        self.repeat_until_edit = QDateTimeEdit()
        self.repeat_until_edit.setCalendarPopup(True)
        repeat_until_dt = item.repeat_until or datetime.now(timezone.utc)
        self.repeat_until_edit.setDateTime(
            QDateTime(
                repeat_until_dt.year,
                repeat_until_dt.month,
                repeat_until_dt.day,
                repeat_until_dt.hour,
                repeat_until_dt.minute,
            )
        )
        self.repeat_until_edit.setEnabled(self.repeat_until_enabled.isChecked())
        self.repeat_until_enabled.toggled.connect(self.repeat_until_edit.setEnabled)
        repeat_until_row = QHBoxLayout()
        repeat_until_row.addWidget(self.repeat_until_enabled)
        repeat_until_row.addWidget(self.repeat_until_edit)
        form.addRow("Repeat Until:", repeat_until_row)

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
        
        # Links section - extract URLs from description and saved link list
        links = self._extract_links(item.description or "")
        links.extend(self._parse_links_text(item.links or ""))
        links = list(dict.fromkeys([url for url in links if url]))
        if links:
            links_label = QLabel()
            links_label.setOpenExternalLinks(False)
            links_label.linkActivated.connect(self._open_link)
            links_html = "<br>".join([f'<a href="{url}" style="color: #5c85d6;">{url[:50]}{"..." if len(url) > 50 else ""}</a>' for url in links[:5]])
            links_label.setText(links_html)
            links_label.setStyleSheet("padding: 4px;")
            form.addRow("Links:", links_label)
        
        # Links input field
        self.links_edit = QTextEdit("\n".join(self._parse_links_text(item.links or "")))
        self.links_edit.setPlaceholderText("Add links (one per line or comma-separated)")
        self.links_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 4px;"
        )
        self.links_edit.setMaximumHeight(80)
        form.addRow("Add Links:", self.links_edit)

        layout.addLayout(form)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Delete button on the left
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(
            "QPushButton { background-color: #8b3a3a; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; } QPushButton:hover { background-color: #a04a4a; }"
        )
        delete_btn.clicked.connect(self._delete_item)
        buttons_layout.addWidget(delete_btn)
        
        # Duplicate button
        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.setStyleSheet(
            "QPushButton { background-color: #3a5a7a; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; } QPushButton:hover { background-color: #4a6a8a; }"
        )
        duplicate_btn.clicked.connect(lambda: self._duplicate_item(item))
        buttons_layout.addWidget(duplicate_btn)
        
        buttons_layout.addStretch()
        
        # Save/Cancel on the right
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_changes)
        button_box.rejected.connect(self.reject)
        buttons_layout.addWidget(button_box)
        
        layout.addLayout(buttons_layout)
        
        # Store item data for duplication
        self._item_data = {
            'title': item.title,
            'description': item.description,
            'type': item.type,
            'status': item.status,
            'scenario': item.scenario.name if item.scenario else None,
            'tags': ', '.join(tag.name for tag in item.tags) if item.tags else '',
            'estimated_time': item.estimated_time,
            'workload': item.workload,
            'start_time': item.start_time,
            'deadline': item.deadline,
            'repeat_pattern': item.repeat_pattern,
            'repeat_until': item.repeat_until,
        }

    def _delete_item(self):
        """Delete the item after confirmation."""
        reply = QMessageBox.question(
            self,
            "Delete Item",
            "Are you sure you want to delete this item? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            with SessionLocal() as session:
                item = session.query(Item).filter(Item.id == self.item_id).first()
                if item:
                    session.delete(item)
                    session.commit()
            self.accept()

    def _duplicate_item(self, item: Item):
        """Open NewItemDialog with item data pre-filled for duplication."""
        self.reject()  # Close this dialog
        
        template_data = {
            'title': f"{self._item_data['title']} (Copy)",
            'description': self._item_data['description'],
            'type': self._item_data['type'],
            'scenario': self._item_data['scenario'],
            'tags': self._item_data['tags'],
            'estimated_time': self._item_data['estimated_time'],
            'workload': self._item_data['workload'],
        }
        
        dialog = NewItemDialog(self._item_data['status'], self.parent(), template_data)
        dialog.setWindowTitle("Duplicate Item")
        if dialog.exec():
            # Refresh will happen via parent
            pass

    def save_changes(self):
        """Save changes to the database."""
        try:
            with SessionLocal() as session:
                item = session.query(Item).filter(Item.id == self.item_id).first()
                if not item:
                    QMessageBox.warning(self, "Save Failed", "The item no longer exists.")
                    return
                item.title = self.title_edit.text().strip()[:255]
                item.description = self.description_edit.toPlainText().strip()
                item.links = self._serialize_links(self.links_edit.toPlainText())
                item.start_time = self._widget_datetime(self.start_time_edit) if self.start_time_enabled.isChecked() else None
                item.deadline = self._widget_datetime(self.deadline_edit) if self.deadline_enabled.isChecked() else None
                item.repeat_pattern = self.repeat_combo.currentData()
                item.repeat_until = self._widget_datetime(self.repeat_until_edit) if self.repeat_until_enabled.isChecked() else None
                if item.start_time and item.estimated_time and (not item.end_time or item.end_time <= item.start_time):
                    settings = load_settings()
                    buffer_per_hour = settings.get("buffer_time_per_hour", 45)
                    duration = item.estimated_time + calculate_buffer_minutes(
                        item.estimated_time, item.workload, buffer_per_hour
                    )
                    item.end_time = item.start_time + timedelta(minutes=max(15, duration))
                self._save_emergency_level(session, item)
                session.commit()
        except SQLAlchemyError as exc:
            QMessageBox.critical(self, "Save Failed", f"Could not save changes.\n\n{exc}")
            return
        self.accept()

    def _extract_links(self, text: str) -> list[str]:
        """Extract URLs from text."""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

    @staticmethod
    def _widget_datetime(widget: QDateTimeEdit) -> datetime:
        dt = widget.dateTime().toPyDateTime()
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    @staticmethod
    def _parse_links_text(raw: str) -> list[str]:
        text = (raw or "").strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(link).strip() for link in parsed if str(link).strip()]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        normalized = text.replace(",", "\n")
        return [part.strip() for part in normalized.splitlines() if part.strip()]

    @staticmethod
    def _serialize_links(raw: str) -> str:
        links = ItemDetailsDialog._parse_links_text(raw)
        return json.dumps(links)

    def _open_link(self, raw_url: str) -> None:
        value = (raw_url or "").strip()
        if not value:
            return
        if value.startswith("file://"):
            url = QUrl(value)
        elif value.startswith("/") or value.startswith("~"):
            path = Path(value).expanduser().resolve()
            url = QUrl.fromLocalFile(str(path))
        else:
            url = QUrl.fromUserInput(value)
        if not url.isValid():
            QMessageBox.warning(self, "Link", f"Invalid link: {value}")
            return
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(self, "Link", f"Could not open link:\n{value}")

    def _save_emergency_level(self, session: Session, item: Item) -> None:
        """Update the item's emergency level tag based on selection."""
        if not self.level_combo:
            return
        selected = self.level_combo.currentText()
        # Remove old level tags
        for tag in list(item.tags):
            if tag.name.startswith(_LEVEL_PREFIX):
                item.tags.remove(tag)
        if selected == "None":
            return
        tag_name = f"{_LEVEL_PREFIX}{selected}"
        tag = session.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            color = _level_color(selected, self._levels) or "#d65c5c"
            tag = Tag(name=tag_name, color=color)
        item.tags.append(tag)


class NewItemDialog(QDialog):
    """Dialog for creating a new item directly in a Kanban column."""

    def __init__(self, status: ItemStatus, parent: QWidget | None = None, template_data: dict | None = None):
        super().__init__(parent)
        self._status = status
        self._template_data = template_data or {}
        self.setWindowTitle(f"New Item - {status.value}")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Template selector at the top
        template_row = QHBoxLayout()
        template_label = QLabel("Template:")
        template_label.setStyleSheet("color: #a0a0b0;")
        template_row.addWidget(template_label)
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("None", None)
        with SessionLocal() as session:
            templates = session.query(ItemTemplate).order_by(ItemTemplate.name).all()
            for t in templates:
                self.template_combo.addItem(t.name, t.id)
        self.template_combo.currentIndexChanged.connect(self._load_template)
        self.template_combo.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 4px;"
        )
        template_row.addWidget(self.template_combo)
        template_row.addStretch()
        layout.addLayout(template_row)

        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter item title...")
        self.title_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 6px;"
        )
        if self._template_data.get('title'):
            self.title_edit.setText(self._template_data['title'])
        form.addRow("Title:", self.title_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Optional description...")
        self.description_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 4px;"
        )
        self.description_edit.setMaximumHeight(80)
        if self._template_data.get('description'):
            self.description_edit.setPlainText(self._template_data['description'])
        form.addRow("Description:", self.description_edit)

        # Type selector
        self.type_combo = QComboBox()
        for item_type in ItemType:
            emoji = {"Task": "📋", "Event": "📅", "Note": "📝", "Goal": "🎯"}.get(item_type.value, "📋")
            self.type_combo.addItem(f"{emoji} {item_type.value}", item_type)
        self.type_combo.setCurrentIndex(0)
        if self._template_data.get('type'):
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == self._template_data['type']:
                    self.type_combo.setCurrentIndex(i)
                    break
        form.addRow("Type:", self.type_combo)

        # Scenario selector
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItem("None")
        with SessionLocal() as session:
            scenarios = session.query(Scenario).order_by(Scenario.name).all()
            for s in scenarios:
                self.scenario_combo.addItem(s.name)
        if self._template_data.get('scenario'):
            idx = self.scenario_combo.findText(self._template_data['scenario'])
            if idx >= 0:
                self.scenario_combo.setCurrentIndex(idx)
        form.addRow("Scenario:", self.scenario_combo)

        # Start time
        self.start_time_enabled = QCheckBox("Set start time")
        start_dt = self._template_data.get("start_time")
        if not start_dt and self._template_data.get("start_date") is not None:
            qdate = self._template_data.get("start_date")
            start_dt = datetime(qdate.year(), qdate.month(), qdate.day(), 9, 0, tzinfo=timezone.utc)
        self.start_time_enabled.setChecked(bool(start_dt))
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setCalendarPopup(True)
        start_default = start_dt or datetime.now(timezone.utc)
        self.start_time_edit.setDateTime(
            QDateTime(
                start_default.year,
                start_default.month,
                start_default.day,
                start_default.hour,
                start_default.minute,
            )
        )
        self.start_time_edit.setEnabled(self.start_time_enabled.isChecked())
        self.start_time_enabled.toggled.connect(self.start_time_edit.setEnabled)
        start_row = QHBoxLayout()
        start_row.addWidget(self.start_time_enabled)
        start_row.addWidget(self.start_time_edit)
        form.addRow("Start:", start_row)

        # Deadline
        self.deadline_enabled = QCheckBox("Set deadline")
        deadline_dt = self._template_data.get("deadline")
        self.deadline_enabled.setChecked(bool(deadline_dt))
        self.deadline_edit = QDateTimeEdit()
        self.deadline_edit.setCalendarPopup(True)
        deadline_default = deadline_dt or datetime.now(timezone.utc)
        self.deadline_edit.setDateTime(
            QDateTime(
                deadline_default.year,
                deadline_default.month,
                deadline_default.day,
                deadline_default.hour,
                deadline_default.minute,
            )
        )
        self.deadline_edit.setEnabled(self.deadline_enabled.isChecked())
        self.deadline_enabled.toggled.connect(self.deadline_edit.setEnabled)
        deadline_row = QHBoxLayout()
        deadline_row.addWidget(self.deadline_enabled)
        deadline_row.addWidget(self.deadline_edit)
        form.addRow("Deadline:", deadline_row)

        # Repeat schedule
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItem("None", None)
        self.repeat_combo.addItem("Daily", "daily")
        self.repeat_combo.addItem("Weekly", "weekly")
        self.repeat_combo.addItem("Monthly", "monthly")
        pattern = (self._template_data.get("repeat_pattern") or "").strip().lower()
        for idx in range(self.repeat_combo.count()):
            if (self.repeat_combo.itemData(idx) or "") == pattern:
                self.repeat_combo.setCurrentIndex(idx)
                break
        form.addRow("Repeat:", self.repeat_combo)

        self.repeat_until_enabled = QCheckBox("Set repeat end")
        repeat_until_dt = self._template_data.get("repeat_until")
        self.repeat_until_enabled.setChecked(bool(repeat_until_dt))
        self.repeat_until_edit = QDateTimeEdit()
        self.repeat_until_edit.setCalendarPopup(True)
        repeat_until_default = repeat_until_dt or datetime.now(timezone.utc)
        self.repeat_until_edit.setDateTime(
            QDateTime(
                repeat_until_default.year,
                repeat_until_default.month,
                repeat_until_default.day,
                repeat_until_default.hour,
                repeat_until_default.minute,
            )
        )
        self.repeat_until_edit.setEnabled(self.repeat_until_enabled.isChecked())
        self.repeat_until_enabled.toggled.connect(self.repeat_until_edit.setEnabled)
        repeat_until_row = QHBoxLayout()
        repeat_until_row.addWidget(self.repeat_until_enabled)
        repeat_until_row.addWidget(self.repeat_until_edit)
        form.addRow("Repeat Until:", repeat_until_row)

        # Estimated time (minutes)
        time_row = QHBoxLayout()
        self.estimated_time_edit = QSpinBox()
        self.estimated_time_edit.setRange(0, 9999)
        self.estimated_time_edit.setSuffix(" min")
        self.estimated_time_edit.setSpecialValueText("Not set")
        self.estimated_time_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 4px;"
        )
        if self._template_data.get('estimated_time'):
            self.estimated_time_edit.setValue(self._template_data['estimated_time'])
        time_row.addWidget(self.estimated_time_edit)
        
        # Buffer time indicator
        self.buffer_label = QLabel("(+0 min buffer)")
        self.buffer_label.setStyleSheet("color: #808090; font-size: 11px;")
        self.estimated_time_edit.valueChanged.connect(self._update_buffer_label)
        time_row.addWidget(self.buffer_label)
        time_row.addStretch()
        form.addRow("Est. Time:", time_row)

        # Workload (1-5 scale)
        workload_row = QHBoxLayout()
        self.workload_combo = QComboBox()
        self.workload_combo.addItem("Not set", 0)
        workload_labels = ["① Light", "② Moderate", "③ Medium", "④ Heavy", "⑤ Very Heavy"]
        for i, label in enumerate(workload_labels, 1):
            self.workload_combo.addItem(label, i)
        if self._template_data.get('workload'):
            self.workload_combo.setCurrentIndex(self._template_data['workload'])
        self.workload_combo.currentIndexChanged.connect(
            lambda _: self._update_buffer_label(self.estimated_time_edit.value())
        )
        workload_row.addWidget(self.workload_combo)
        workload_row.addStretch()
        form.addRow("Workload:", workload_row)

        # Tags input
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by comma (e.g., #urgent, #work)")
        self.tags_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 6px;"
        )
        if self._template_data.get('tags'):
            self.tags_edit.setText(self._template_data['tags'])
        form.addRow("Tags:", self.tags_edit)
        
        # Existing tags for quick selection
        self.tags_buttons_layout = QHBoxLayout()
        with SessionLocal() as session:
            existing_tags = session.query(Tag).order_by(Tag.name).limit(8).all()
            for tag in existing_tags:
                btn = QPushButton(tag.name)
                btn.setStyleSheet(
                    f"background-color: {tag.color}; color: white; border-radius: 10px;"
                    "padding: 2px 8px; font-size: 10px;"
                )
                btn.setFixedHeight(20)
                btn.clicked.connect(lambda checked, t=tag.name: self._add_tag(t))
                self.tags_buttons_layout.addWidget(btn)
        self.tags_buttons_layout.addStretch()
        form.addRow("", self.tags_buttons_layout)

        layout.addLayout(form)

        # Buttons
        button_row = QHBoxLayout()
        
        save_template_btn = QPushButton("Save as Template")
        save_template_btn.setStyleSheet(
            "background-color: #3a5a7a; color: #e0e0e0; border-radius: 4px; padding: 6px 12px;"
        )
        save_template_btn.clicked.connect(self._save_as_template)
        button_row.addWidget(save_template_btn)
        
        button_row.addStretch()
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._create_item)
        button_box.rejected.connect(self.reject)
        button_row.addWidget(button_box)
        
        layout.addLayout(button_row)
        
        self._update_buffer_label(self.estimated_time_edit.value())

    def _add_tag(self, tag_name: str):
        """Add a tag to the tags input."""
        current = self.tags_edit.text().strip()
        if current:
            if tag_name not in current:
                self.tags_edit.setText(f"{current}, {tag_name}")
        else:
            self.tags_edit.setText(tag_name)

    def _load_template(self, index: int):
        """Load a template into the form fields."""
        template_id = self.template_combo.itemData(index)
        if not template_id:
            return
        
        with SessionLocal() as session:
            template = session.query(ItemTemplate).filter(ItemTemplate.id == template_id).first()
            if template:
                if template.title_template:
                    self.title_edit.setText(template.title_template)
                if template.description_template:
                    self.description_edit.setPlainText(template.description_template)
                # Set type
                for i in range(self.type_combo.count()):
                    if self.type_combo.itemData(i) == template.type:
                        self.type_combo.setCurrentIndex(i)
                        break
                # Set scenario
                if template.scenario:
                    idx = self.scenario_combo.findText(template.scenario.name)
                    if idx >= 0:
                        self.scenario_combo.setCurrentIndex(idx)
                if template.estimated_time:
                    self.estimated_time_edit.setValue(template.estimated_time)
                if template.workload:
                    self.workload_combo.setCurrentIndex(template.workload)
                if template.tag_names:
                    self.tags_edit.setText(template.tag_names)

    def _save_as_template(self):
        """Save current form values as a template."""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self, "Save Template", "Enter template name:",
            QLineEdit.EchoMode.Normal, ""
        )
        if not ok or not name.strip():
            return
        
        name = name.strip()
        
        with SessionLocal() as session:
            # Check if template exists
            existing = session.query(ItemTemplate).filter(ItemTemplate.name == name).first()
            if existing:
                reply = QMessageBox.question(
                    self, "Template Exists",
                    f"Template '{name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                template = existing
            else:
                template = ItemTemplate(name=name)
                session.add(template)
            
            template.title_template = self.title_edit.text().strip()
            template.description_template = self.description_edit.toPlainText().strip()
            template.type = self.type_combo.currentData()
            template.status = self._status
            template.estimated_time = self.estimated_time_edit.value() if self.estimated_time_edit.value() > 0 else None
            template.workload = self.workload_combo.currentData() if self.workload_combo.currentData() > 0 else None
            
            scenario_name = self.scenario_combo.currentText()
            if scenario_name != "None":
                scenario = session.query(Scenario).filter(Scenario.name == scenario_name).first()
                template.scenario_id = scenario.id if scenario else None
            else:
                template.scenario_id = None
            
            template.tag_names = self.tags_edit.text().strip()
            
            session.commit()
            
            # Add to combo if new
            if not existing:
                self.template_combo.addItem(name, template.id)
            
            QMessageBox.information(self, "Saved", f"Template '{name}' saved!")

    def _update_buffer_label(self, minutes: int):
        """Update the buffer time label."""
        settings = load_settings()
        buffer_per_hour = settings.get("buffer_time_per_hour", 45)
        workload = self.workload_combo.currentData() if hasattr(self, "workload_combo") else None
        if minutes > 0:
            buffer = calculate_buffer_minutes(minutes, workload, buffer_per_hour)
            self.buffer_label.setText(f"(+{buffer} min buffer)")
        else:
            self.buffer_label.setText("(+0 min buffer)")

    @staticmethod
    def _widget_datetime(widget: QDateTimeEdit) -> datetime:
        dt = widget.dateTime().toPyDateTime()
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    def _create_item(self):
        """Create the new item in the database."""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Required", "Please enter a title.")
            return

        try:
            with SessionLocal() as session:
                scenario = None
                scenario_name = self.scenario_combo.currentText()
                if scenario_name != "None":
                    scenario = session.query(Scenario).filter(Scenario.name == scenario_name).first()

                item_type = self.type_combo.currentData()

                estimated_time = self.estimated_time_edit.value() if self.estimated_time_edit.value() > 0 else None
                workload = self.workload_combo.currentData() if self.workload_combo.currentData() > 0 else None
                start_time = self._widget_datetime(self.start_time_edit) if self.start_time_enabled.isChecked() else None
                deadline = self._widget_datetime(self.deadline_edit) if self.deadline_enabled.isChecked() else None
                repeat_pattern = self.repeat_combo.currentData()
                repeat_until = self._widget_datetime(self.repeat_until_edit) if self.repeat_until_enabled.isChecked() else None
                end_time = None
                if start_time and estimated_time:
                    settings = load_settings()
                    buffer_per_hour = settings.get("buffer_time_per_hour", 45)
                    duration_min = estimated_time + calculate_buffer_minutes(
                        estimated_time, workload, buffer_per_hour
                    )
                    end_time = start_time + timedelta(minutes=max(15, duration_min))

                item = Item(
                    title=title[:255],
                    description=self.description_edit.toPlainText().strip(),
                    type=item_type,
                    status=self._status,
                    scenario=scenario,
                    estimated_time=estimated_time,
                    workload=workload,
                    start_time=start_time,
                    end_time=end_time,
                    deadline=deadline,
                    repeat_pattern=repeat_pattern,
                    repeat_until=repeat_until,
                )
                session.add(item)
                session.flush()  # Get the item ID

                # Handle tags
                tags_text = self.tags_edit.text().strip()
                if tags_text:
                    tag_names = [t.strip() for t in tags_text.split(',') if t.strip()]
                    for tag_name in tag_names:
                        # Ensure tag starts with #
                        if not tag_name.startswith('#'):
                            tag_name = f'#{tag_name}'
                        # Find or create tag
                        tag = session.query(Tag).filter(Tag.name == tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            session.add(tag)
                        item.tags.append(tag)

                session.commit()
        except SQLAlchemyError as exc:
            QMessageBox.critical(self, "Create Failed", f"Could not create item.\n\n{exc}")
            return

        self.accept()


class KanbanColumn(QWidget):
    """A single Kanban column with a header and a scrollable card area."""

    def __init__(self, status: ItemStatus, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status = status
        self._count_label: QLabel | None = None
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header with title, count badge, and add button
        header = QWidget()
        color = _COLUMN_COLORS.get(self._status, "#4a4a4a")
        header.setStyleSheet(
            f"background-color: {color}; border-top-left-radius: 6px; border-top-right-radius: 6px;"
        )
        header.setFixedHeight(44)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)
        
        title_label = QLabel(self._status.value)
        title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; background: transparent;")
        header_layout.addWidget(title_label)
        
        # Count badge
        self._count_label = QLabel("0")
        self._count_label.setStyleSheet(
            "background-color: rgba(255,255,255,0.2); color: #ffffff; font-size: 11px;"
            "padding: 2px 6px; border-radius: 8px;"
        )
        header_layout.addWidget(self._count_label)
        
        header_layout.addStretch()
        
        # Add button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setStyleSheet(
            "QPushButton { background-color: rgba(255,255,255,0.2); color: #ffffff; border-radius: 12px;"
            " font-size: 16px; font-weight: bold; border: none; }"
            "QPushButton:hover { background-color: rgba(255,255,255,0.3); }"
        )
        add_btn.setToolTip(f"Add new item to {self._status.value}")
        add_btn.clicked.connect(self._add_new_item)
        header_layout.addWidget(add_btn)
        
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

    def _add_new_item(self):
        """Open a dialog to create a new item in this column."""
        dialog = NewItemDialog(self._status, self)
        if dialog.exec():
            todos_page = self.find_todos_page()
            if todos_page:
                todos_page.refresh_current()

    def set_cards(self, cards_data: list[tuple[str, int, str | None, str | None, str | None]]) -> None:
        """Replace the column content with the provided cards.
        
        cards_data: list of (text, item_id, accent_color, deadline_status, scenario_color) tuples.
        """
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Update count badge
        if self._count_label:
            self._count_label.setText(str(len(cards_data)))

        if not cards_data:
            self._add_placeholder()
            return

        for text, item_id, accent, deadline_status, scenario_color in cards_data:
            self._add_card(text, item_id, accent, deadline_status, scenario_color)

    def _add_card(self, text: str, item_id: int, accent: str | None, deadline_status: str | None = None, scenario_color: str | None = None) -> None:
        """Add a draggable card to the column."""
        card = DraggableCard(text, item_id, accent, deadline_status, scenario_color)
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

        # Title row with batch edit button
        title_row = QHBoxLayout()
        title = QLabel("TODOs — Action Hub")
        title.setStyleSheet("color: #c8c8d8; font-size: 18px; font-weight: bold;")
        title_row.addWidget(title)
        
        title_row.addStretch()
        
        # Batch edit button (hidden by default)
        self._batch_edit_btn = QPushButton("Edit Selected (0)")
        self._batch_edit_btn.setStyleSheet(
            "QPushButton { background-color: #5c85d6; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; } QPushButton:hover { background-color: #6a95e6; }"
        )
        self._batch_edit_btn.clicked.connect(self._open_batch_edit)
        self._batch_edit_btn.hide()
        title_row.addWidget(self._batch_edit_btn)
        
        # Clear selection button
        self._clear_selection_btn = QPushButton("Clear Selection")
        self._clear_selection_btn.setStyleSheet(
            "QPushButton { background-color: #4a4a5a; color: #c0c0d0; border-radius: 4px;"
            " padding: 6px 12px; } QPushButton:hover { background-color: #5a5a6a; }"
        )
        self._clear_selection_btn.clicked.connect(self._clear_all_card_selections)
        self._clear_selection_btn.hide()
        title_row.addWidget(self._clear_selection_btn)
        
        root.addLayout(title_row)

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
        levels = _load_emergency_levels()
        now = datetime.now(timezone.utc)
        cards: dict[ItemStatus, list[tuple[str, int, str | None, str | None, str | None]]] = {status: [] for status in ItemStatus}
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
                
                # Determine deadline status
                deadline_status = None
                if item.deadline:
                    deadline_tz = item.deadline if item.deadline.tzinfo else item.deadline.replace(tzinfo=timezone.utc)
                    parts.append(f"Deadline: {item.deadline.strftime('%b %d, %H:%M')}")
                    if deadline_tz < now:
                        deadline_status = "overdue"
                        parts.append("⚠️ OVERDUE")
                    elif (deadline_tz - now).total_seconds() < 86400:  # < 24 hours
                        deadline_status = "urgent"
                        parts.append("⏰ Due soon")
                
                level = _level_from_tags(item.tags)
                level_color = _level_color(level, levels)
                if level:
                    parts.append(f"Emergency: {level}")
                if item.tags:
                    tags = ", ".join(tag.name for tag in item.tags if not tag.name.startswith(_LEVEL_PREFIX))
                    if tags:
                        parts.append(f"Tags: {tags}")
                
                # Get scenario color
                scenario_color = item.scenario.color if item.scenario else None
                
                cards[item.status].append(("\n".join(parts), item.id, level_color, deadline_status, scenario_color))

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

    # ------------------------------------------------------------------
    # Multi-select & Batch Edit
    # ------------------------------------------------------------------
    def _update_batch_edit_button(self) -> None:
        """Update the batch edit button visibility and count."""
        count = len(DraggableCard._selected_items)
        if count > 0:
            self._batch_edit_btn.setText(f"Edit Selected ({count})")
            self._batch_edit_btn.show()
            self._clear_selection_btn.show()
        else:
            self._batch_edit_btn.hide()
            self._clear_selection_btn.hide()

    def _clear_all_card_selections(self) -> None:
        """Clear selection from all cards."""
        DraggableCard._selected_items.clear()
        # Update all card styles
        for status, column in self._columns.items():
            scroll_area = column.findChild(QScrollArea)
            if scroll_area:
                container = scroll_area.widget()
                if container:
                    for i in range(container.layout().count()):
                        item = container.layout().itemAt(i)
                        if item and item.widget():
                            card = item.widget()
                            if isinstance(card, DraggableCard):
                                card._is_selected = False
                                card._update_style()
        self._update_batch_edit_button()

    def _open_batch_edit(self) -> None:
        """Open batch edit dialog for selected items."""
        selected_ids = list(DraggableCard._selected_items)
        if not selected_ids:
            return
        
        dialog = BatchEditDialog(selected_ids, self)
        if dialog.exec():
            self._clear_all_card_selections()
            self.refresh_current()


class BatchEditDialog(QDialog):
    """Dialog for batch editing multiple items."""

    def __init__(self, item_ids: list[int], parent: QWidget | None = None):
        super().__init__(parent)
        self._item_ids = item_ids
        self.setWindowTitle(f"Batch Edit - {len(item_ids)} items")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(f"Editing {len(self._item_ids)} selected items.\nOnly checked fields will be updated.")
        info.setStyleSheet("color: #a0a0b0; font-size: 11px; padding: 8px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()

        # Status change
        self.status_check = QPushButton("☐ Status")
        self.status_check.setCheckable(True)
        self.status_check.setStyleSheet("text-align: left; padding: 4px;")
        self.status_combo = QComboBox()
        for status in ItemStatus:
            self.status_combo.addItem(status.value, status)
        self.status_combo.setEnabled(False)
        self.status_check.toggled.connect(self.status_combo.setEnabled)
        self.status_check.toggled.connect(lambda c: self.status_check.setText("☑ Status" if c else "☐ Status"))
        row = QHBoxLayout()
        row.addWidget(self.status_check)
        row.addWidget(self.status_combo)
        form.addRow(row)

        # Emergency level
        self.level_check = QPushButton("☐ Emergency")
        self.level_check.setCheckable(True)
        self.level_check.setStyleSheet("text-align: left; padding: 4px;")
        self.level_combo = QComboBox()
        self.level_combo.addItem("None")
        for level in _load_emergency_levels():
            self.level_combo.addItem(level["name"])
        self.level_combo.setEnabled(False)
        self.level_check.toggled.connect(self.level_combo.setEnabled)
        self.level_check.toggled.connect(lambda c: self.level_check.setText("☑ Emergency" if c else "☐ Emergency"))
        row = QHBoxLayout()
        row.addWidget(self.level_check)
        row.addWidget(self.level_combo)
        form.addRow(row)

        # Workload
        self.workload_check = QPushButton("☐ Workload")
        self.workload_check.setCheckable(True)
        self.workload_check.setStyleSheet("text-align: left; padding: 4px;")
        self.workload_combo = QComboBox()
        self.workload_combo.addItem("Not set", 0)
        workload_labels = ["① Light", "② Moderate", "③ Medium", "④ Heavy", "⑤ Very Heavy"]
        for i, label in enumerate(workload_labels, 1):
            self.workload_combo.addItem(label, i)
        self.workload_combo.setEnabled(False)
        self.workload_check.toggled.connect(self.workload_combo.setEnabled)
        self.workload_check.toggled.connect(lambda c: self.workload_check.setText("☑ Workload" if c else "☐ Workload"))
        row = QHBoxLayout()
        row.addWidget(self.workload_check)
        row.addWidget(self.workload_combo)
        form.addRow(row)

        # Add tags
        self.add_tags_check = QPushButton("☐ Add Tags")
        self.add_tags_check.setCheckable(True)
        self.add_tags_check.setStyleSheet("text-align: left; padding: 4px;")
        self.add_tags_edit = QLineEdit()
        self.add_tags_edit.setPlaceholderText("Tags to add (comma separated)")
        self.add_tags_edit.setEnabled(False)
        self.add_tags_check.toggled.connect(self.add_tags_edit.setEnabled)
        self.add_tags_check.toggled.connect(lambda c: self.add_tags_check.setText("☑ Add Tags" if c else "☐ Add Tags"))
        row = QHBoxLayout()
        row.addWidget(self.add_tags_check)
        row.addWidget(self.add_tags_edit)
        form.addRow(row)

        layout.addLayout(form)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _apply_changes(self):
        """Apply batch changes to all selected items."""
        with SessionLocal() as session:
            items = session.query(Item).filter(Item.id.in_(self._item_ids)).all()
            
            for item in items:
                # Update status
                if self.status_check.isChecked():
                    item.status = self.status_combo.currentData()
                
                # Update workload
                if self.workload_check.isChecked():
                    workload = self.workload_combo.currentData()
                    item.workload = workload if workload > 0 else None
                
                # Update emergency level
                if self.level_check.isChecked():
                    selected = self.level_combo.currentText()
                    # Remove old level tags
                    for tag in list(item.tags):
                        if tag.name.startswith(_LEVEL_PREFIX):
                            item.tags.remove(tag)
                    if selected != "None":
                        tag_name = f"{_LEVEL_PREFIX}{selected}"
                        tag = session.query(Tag).filter(Tag.name == tag_name).first()
                        if not tag:
                            levels = _load_emergency_levels()
                            color = _level_color(selected, levels) or "#d65c5c"
                            tag = Tag(name=tag_name, color=color)
                        item.tags.append(tag)
                
                # Add tags
                if self.add_tags_check.isChecked():
                    tags_text = self.add_tags_edit.text().strip()
                    if tags_text:
                        tag_names = [t.strip() for t in tags_text.split(',') if t.strip()]
                        for tag_name in tag_names:
                            if not tag_name.startswith('#'):
                                tag_name = f'#{tag_name}'
                            tag = session.query(Tag).filter(Tag.name == tag_name).first()
                            if not tag:
                                tag = Tag(name=tag_name)
                                session.add(tag)
                            if tag not in item.tags:
                                item.tags.append(tag)
            
            session.commit()
        
        self.accept()
