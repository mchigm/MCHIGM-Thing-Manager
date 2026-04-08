"""
Plan page — Roadmap / Gantt view & Weekly Retrospective.

Phase 5 adds lightweight Gantt rendering, PDF export, and a real retrospective modal.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPageSize, QPainter, QPen, QPdfWriter
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QFileDialog,
    QMenu,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from src.database.models import Dependency, Item, ItemStatus, Scenario, SessionLocal, Tag
from src.ui.search_filters import parse_search_text
from src.ui.pages.todos import ItemDetailsDialog

_STATUS_COLOR = {
    ItemStatus.BACKLOG: QColor("#4a4a5a"),
    ItemStatus.TODO: QColor("#3a5a7a"),
    ItemStatus.DOING: QColor("#5a4a7a"),
    ItemStatus.DONE: QColor("#3a6a4a"),
}
_ROW_HEIGHT = 48
_PADDING = 30
_DAY_WIDTH = 180
_MIN_ZOOM = 80
_MAX_ZOOM = 300
_BAR_HEIGHT = 28


class PlanBarItem(QGraphicsRectItem):
    """Interactive roadmap bar with drag, edit, and context actions."""

    def __init__(
        self,
        item: Item,
        start: datetime,
        end: datetime,
        baseline: datetime,
        day_width: float,
        x: float,
        y: float,
        pen: QPen,
        color: QColor,
        refresh_cb,
    ) -> None:
        width = max(80.0, (end - start).total_seconds() / 86400 * day_width)
        super().__init__(0, 0, width, _BAR_HEIGHT)
        self._item_id = item.id
        self._duration = end - start
        self._baseline = baseline
        self._day_width = day_width
        self._row_y = y
        self._refresh_cb = refresh_cb
        self.setPos(x, y)
        self.setPen(pen)
        self.setBrush(color)
        self.setZValue(1)
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip(
            f"{item.title}\n"
            f"Start: {start.strftime('%Y-%m-%d %H:%M')}  •  "
            f"End: {end.strftime('%Y-%m-%d %H:%M')}\n"
            f"Status: {item.status.value}  •  Type: {item.type.value}"
        )

        label = QGraphicsSimpleTextItem(item.title[:30] + ("..." if len(item.title) > 30 else ""), self)
        label.setBrush(Qt.GlobalColor.white)
        label.setPos(6, (_BAR_HEIGHT - 14) / 2)  # Center vertically
        self._press_x = x

    def itemChange(self, change, value):
        """Lock movement to the row while allowing horizontal drag."""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            clamped_x = max(_PADDING, new_pos.x())
            return QPointF(clamped_x, self._row_y)
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self._press_x = self.pos().x()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if abs(self.pos().x() - self._press_x) > 1:
            self._persist_move()

    def mouseDoubleClickEvent(self, event):
        self._open_details()
        event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu()
        open_action = menu.addAction("Open Details")
        mark_done = menu.addAction("Mark as Done")
        move_today = menu.addAction("Move to Today")
        chosen = menu.exec(event.screenPos())
        if chosen == open_action:
            self._open_details()
        elif chosen == mark_done:
            self._set_status_done()
        elif chosen == move_today:
            self._move_to_today()
        event.accept()

    def _open_details(self) -> None:
        with SessionLocal() as session:
            item = session.get(Item, self._item_id)
            if not item:
                return
            session.expunge(item)
        dialog = ItemDetailsDialog(item)
        if dialog.exec():
            self._refresh_cb()

    def _persist_move(self) -> None:
        new_start = self._baseline + timedelta(days=(self.pos().x() - _PADDING) / self._day_width)
        new_end = new_start + self._duration
        with SessionLocal() as session:
            item = session.get(Item, self._item_id)
            if not item:
                return
            item.start_time = new_start
            item.end_time = new_end
            session.commit()
        self._refresh_cb()

    def _set_status_done(self) -> None:
        with SessionLocal() as session:
            item = session.get(Item, self._item_id)
            if not item:
                return
            item.status = ItemStatus.DONE
            session.commit()
        self._refresh_cb()

    def _move_to_today(self) -> None:
        today = datetime.now(self._baseline.tzinfo or timezone.utc).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        with SessionLocal() as session:
            item = session.get(Item, self._item_id)
            if not item:
                return
            item.start_time = today
            item.end_time = today + self._duration
            session.commit()
        self._refresh_cb()


class PlanPage(QWidget):
    """Page 4 — Plan / Roadmap & Retrospective."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._day_width = _DAY_WIDTH
        self._current_items: list[Item] = []
        self._current_scenario = "All"
        self._current_search = ""
        self._zoom_value_label: QLabel | None = None
        self._zoom_slider: QSlider | None = None
        self._stats_labels: dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("📊 Plan — Roadmap & Retrospective")
        title.setStyleSheet("color: #c8c8d8; font-size: 18px; font-weight: bold;")
        title_row.addWidget(title)
        title_row.addStretch()

        # Add new item button
        add_btn = QPushButton("+ New Item")
        add_btn.setStyleSheet(
            "QPushButton { background-color: #5cd685; color: #1a1a2e; border-radius: 4px;"
            " padding: 6px 12px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: #6ce695; }"
        )
        add_btn.clicked.connect(self._add_new_item)
        title_row.addWidget(add_btn)

        export_btn = QPushButton("📄 Export PDF")
        export_btn.setStyleSheet(
            "QPushButton { background-color: #3a5a7a; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; font-size: 12px; }"
            "QPushButton:hover { background-color: #4a6a8a; }"
        )
        export_btn.clicked.connect(self._export_pdf)
        title_row.addWidget(export_btn)

        retro_btn = QPushButton("📈 Weekly Retrospective")
        retro_btn.setStyleSheet(
            "QPushButton { background-color: #5a4a7a; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; font-size: 12px; }"
            "QPushButton:hover { background-color: #6a5a8a; }"
        )
        retro_btn.clicked.connect(self._show_retro_placeholder)
        title_row.addWidget(retro_btn)
        root.addLayout(title_row)

        # Statistics panel
        stats_frame = QFrame()
        stats_frame.setStyleSheet(
            "QFrame { background-color: #1a1a2e; border-radius: 8px; border: 1px solid #2a2a3e; }"
        )
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(12, 8, 12, 8)
        stats_layout.setSpacing(20)
        
        # Status counts
        for status in ItemStatus:
            color = _STATUS_COLOR.get(status, QColor("#4a4a5a")).name()
            stat_widget = QWidget()
            stat_vbox = QVBoxLayout(stat_widget)
            stat_vbox.setContentsMargins(0, 0, 0, 0)
            stat_vbox.setSpacing(2)
            
            count_label = QLabel("0")
            count_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._stats_labels[f"count_{status.value}"] = count_label
            stat_vbox.addWidget(count_label)
            
            name_label = QLabel(status.value)
            name_label.setStyleSheet(f"color: #808090; font-size: 10px;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_vbox.addWidget(name_label)
            
            stats_layout.addWidget(stat_widget)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #3a3a4e;")
        stats_layout.addWidget(sep)
        
        # Total workload
        workload_widget = QWidget()
        workload_vbox = QVBoxLayout(workload_widget)
        workload_vbox.setContentsMargins(0, 0, 0, 0)
        workload_vbox.setSpacing(2)
        
        workload_label = QLabel("0h")
        workload_label.setStyleSheet("color: #5cd685; font-size: 20px; font-weight: bold;")
        workload_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_labels["total_time"] = workload_label
        workload_vbox.addWidget(workload_label)
        
        workload_name = QLabel("Est. Time")
        workload_name.setStyleSheet("color: #808090; font-size: 10px;")
        workload_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        workload_vbox.addWidget(workload_name)
        
        stats_layout.addWidget(workload_widget)
        
        # Average workload
        avg_widget = QWidget()
        avg_vbox = QVBoxLayout(avg_widget)
        avg_vbox.setContentsMargins(0, 0, 0, 0)
        avg_vbox.setSpacing(2)
        
        avg_label = QLabel("0")
        avg_label.setStyleSheet("color: #d6b55c; font-size: 20px; font-weight: bold;")
        avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_labels["avg_workload"] = avg_label
        avg_vbox.addWidget(avg_label)
        
        avg_name = QLabel("Avg Workload")
        avg_name.setStyleSheet("color: #808090; font-size: 10px;")
        avg_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avg_vbox.addWidget(avg_name)
        
        stats_layout.addWidget(avg_widget)
        stats_layout.addStretch()
        
        root.addWidget(stats_frame)

        # Timeline controls
        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.setContentsMargins(0, 0, 0, 0)
        
        zoom_label = QLabel("🔍 Scale:")
        zoom_label.setStyleSheet("color: #9aa0b8; font-size: 12px;")
        controls.addWidget(zoom_label)

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(_MIN_ZOOM, _MAX_ZOOM)
        self._zoom_slider.setValue(_DAY_WIDTH)
        self._zoom_slider.setFixedWidth(150)
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        controls.addWidget(self._zoom_slider)

        self._zoom_value_label = QLabel("100%")
        self._zoom_value_label.setStyleSheet("color: #c8c8d8; font-size: 12px;")
        controls.addWidget(self._zoom_value_label)
        
        controls.addSpacing(20)
        
        # Legend
        legend_label = QLabel("Legend:")
        legend_label.setStyleSheet("color: #9aa0b8; font-size: 12px;")
        controls.addWidget(legend_label)
        
        for status in ItemStatus:
            color = _STATUS_COLOR.get(status, QColor("#4a4a5a")).name()
            legend_item = QLabel(f"● {status.value}")
            legend_item.setStyleSheet(f"color: {color}; font-size: 11px;")
            controls.addWidget(legend_item)
        
        controls.addStretch()
        root.addLayout(controls)

        # Gantt view
        self._scene = QGraphicsScene()
        self._scene.setBackgroundBrush(QColor("#0f1222"))

        self._view = QGraphicsView(self._scene)
        self._view.setStyleSheet(
            "background-color: #1e1e2e; border-radius: 6px; border: 1px solid #3a3a4a;"
        )
        self._view.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        root.addWidget(self._view, stretch=1)

    def _update_stats(self, items: list[Item]) -> None:
        """Update the statistics panel with current item data."""
        # Count by status
        status_counts = {status: 0 for status in ItemStatus}
        total_time = 0
        workloads = []
        
        for item in items:
            status_counts[item.status] = status_counts.get(item.status, 0) + 1
            if item.estimated_time:
                total_time += item.estimated_time
            if item.workload:
                workloads.append(item.workload)
        
        # Update labels
        for status in ItemStatus:
            if f"count_{status.value}" in self._stats_labels:
                self._stats_labels[f"count_{status.value}"].setText(str(status_counts.get(status, 0)))
        
        # Total time in hours
        hours = total_time / 60
        if "total_time" in self._stats_labels:
            self._stats_labels["total_time"].setText(f"{hours:.1f}h")
        
        # Average workload
        avg_workload = sum(workloads) / len(workloads) if workloads else 0
        if "avg_workload" in self._stats_labels:
            self._stats_labels["avg_workload"].setText(f"{avg_workload:.1f}")

    def refresh_items(self, scenario_name: str = "All", search_text: str = "") -> None:
        """Reload items and redraw the roadmap."""
        self._current_scenario = scenario_name
        self._current_search = search_text
        items = self._query_items(scenario_name, search_text)
        self._current_items = items
        self._update_stats(items)
        self._render_gantt(items)

    def _refresh_current(self) -> None:
        """Re-run the latest query and redraw."""
        self.refresh_items(self._current_scenario, self._current_search)

    def _query_items(self, scenario_name: str, search_text: str) -> list[Item]:
        filters = parse_search_text(search_text)
        with SessionLocal() as session:
            query = (
                session.query(Item)
                .options(selectinload(Item.parent_links).selectinload(Dependency.parent))
                .outerjoin(Scenario)
            )
            if scenario_name != "All":
                query = query.filter(Scenario.name == scenario_name)
            if filters.tags:
                query = query.filter(Item.tags.any(Tag.name.in_(filters.tags)))
            if filters.statuses:
                query = query.filter(Item.status.in_(filters.statuses))
            for term in filters.terms:
                like = f"%{term}%"
                query = query.filter(or_(Item.title.ilike(like), Item.description.ilike(like)))
            return (
                query.order_by(Item.start_time.is_(None), Item.start_time, Item.deadline, Item.created_at)
                .distinct()
                .all()
            )

    def _render_gantt(self, items: list[Item]) -> None:
        self._scene.clear()
        if not items:
            text = self._scene.addText("No items match the current filters.")
            text.setDefaultTextColor(Qt.GlobalColor.lightGray)
            self._fit_scene()
            return

        start_dates: list[datetime] = []
        end_dates: list[datetime] = []
        for item in items:
            start, end = self._time_window(item)
            start_dates.append(start)
            end_dates.append(end)
        baseline = min(start_dates) if start_dates else datetime.now(timezone.utc)
        now_ts = datetime.now(baseline.tzinfo or timezone.utc)
        latest_end = max(end_dates + [now_ts]) if end_dates else baseline + timedelta(days=1)

        self._draw_time_axis(baseline, latest_end, len(items))

        positions: dict[int, PlanBarItem] = {}
        pen = QPen(QColor("#2e2e42"))

        for idx, item in enumerate(items):
            start, end = self._time_window(item)
            start_days = max(0.0, (start - baseline).total_seconds() / 86400)
            x = _PADDING + start_days * self._day_width
            y = _PADDING + idx * _ROW_HEIGHT
            color = _STATUS_COLOR.get(item.status, QColor("#3c3c50"))

            bar = PlanBarItem(
                item=item,
                start=start,
                end=end,
                baseline=baseline,
                day_width=self._day_width,
                x=x,
                y=y,
                pen=pen,
                color=color,
                refresh_cb=self._refresh_current,
            )
            self._scene.addItem(bar)
            positions[item.id] = bar

        dep_pen = QPen(QColor("#a0a0c0"))
        dep_pen.setWidth(2)
        for item in items:
            if item.id not in positions:
                continue
            child_bar = positions[item.id]
            child_rect = child_bar.rect()
            child_y = child_bar.pos().y() + child_rect.height() / 2
            child_x = child_bar.pos().x()
            for link in item.parent_links:
                parent = link.parent
                if parent and parent.id in positions:
                    parent_bar = positions[parent.id]
                    parent_rect = parent_bar.rect()
                    px = parent_bar.pos().x()
                    py = parent_bar.pos().y()
                    pw = parent_rect.width()
                    self._scene.addLine(px + pw, py + parent_rect.height() / 2, child_x, child_y, dep_pen)

        self._fit_scene()

    def _draw_time_axis(self, baseline: datetime, max_end: datetime, rows: int) -> None:
        """Draw day ticks, grid lines, and a 'Now' marker."""
        span_days = max(1, int((max_end - baseline).total_seconds() / 86400) + 2)
        height = _PADDING + rows * _ROW_HEIGHT + 26
        axis_pen = QPen(QColor("#2f3045"))
        axis_pen.setWidth(1)
        self._scene.addLine(_PADDING, _PADDING - 10, _PADDING + span_days * self._day_width, _PADDING - 10, axis_pen)

        for day in range(span_days):
            tick_x = _PADDING + day * self._day_width
            self._scene.addLine(tick_x, _PADDING - 8, tick_x, height, axis_pen)
            day_label = self._scene.addText((baseline + timedelta(days=day)).strftime("%b %d"))
            day_label.setDefaultTextColor(QColor("#aeb1c7"))
            day_label.setPos(tick_x + 4, _PADDING - 30)

        now = datetime.now(baseline.tzinfo or timezone.utc)
        if baseline <= now <= max_end:
            days_from_base = (now - baseline).total_seconds() / 86400
            x = _PADDING + days_from_base * self._day_width
            now_pen = QPen(QColor("#d65c5c"))
            now_pen.setWidth(2)
            self._scene.addLine(x, _PADDING - 18, x, height, now_pen)
            now_label = self._scene.addText("Now")
            now_label.setDefaultTextColor(QColor("#d65c5c"))
            now_label.setPos(x + 4, _PADDING - 42)

    def _time_window(self, item: Item) -> tuple[datetime, datetime]:
        """Return (start, end) datetimes for rendering."""
        start = item.start_time or item.deadline or item.created_at or datetime.now(timezone.utc)
        end = item.end_time or item.deadline or (start + timedelta(hours=1))
        if end <= start:
            end = start + timedelta(hours=1)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return start, end

    def _on_zoom_changed(self, value: int) -> None:
        """Adjust horizontal scale without re-querying the database."""
        self._day_width = max(_MIN_ZOOM, min(_MAX_ZOOM, value))
        if self._zoom_value_label:
            percent = int(self._day_width / _DAY_WIDTH * 100)
            self._zoom_value_label.setText(f"{percent}%")
        self._render_gantt(self._current_items)

    def _fit_scene(self) -> None:
        rect = self._scene.itemsBoundingRect()
        padded = rect.adjusted(-_PADDING, -_PADDING, _PADDING * 2, _PADDING * 2)
        if padded.isValid():
            self._scene.setSceneRect(padded)
            # Don't auto-fit to view - let user scroll and zoom manually
            # Reset view to show top-left corner at 1:1 scale
            self._view.resetTransform()
            self._view.centerOn(padded.topLeft())

    def _export_pdf(self) -> None:
        """Render the current roadmap scene to a PDF without extra dependencies."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Roadmap as PDF",
            str(Path.home() / "roadmap.pdf"),
            "PDF Files (*.pdf)",
        )
        if not path:
            return
        writer = QPdfWriter(path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        painter = QPainter(writer)
        try:
            source = self._scene.itemsBoundingRect().adjusted(-_PADDING, -_PADDING, _PADDING, _PADDING)
            target = QRectF(0, 0, writer.width(), writer.height())
            self._scene.render(painter, target, source)
            QMessageBox.information(self, "Export", "Roadmap exported to PDF.")
        except Exception as exc:  # pragma: no cover - GUI feedback
            QMessageBox.critical(self, "Export Failed", str(exc))
        finally:
            painter.end()

    def _show_retro_placeholder(self) -> None:
        """Summarize recently completed work."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        recent_data: list[tuple[str, str, str]] = []
        with SessionLocal() as session:
            recent = (
                session.query(Item)
                .options(selectinload(Item.scenario))
                .filter(Item.status == ItemStatus.DONE, Item.updated_at >= week_ago)
                .order_by(Item.updated_at.desc())
                .all()
            )
            for item in recent:
                scenario_name = item.scenario.name if item.scenario else "Unassigned"
                recent_data.append((scenario_name, item.title, item.type.value))

        if not recent_data:
            QMessageBox.information(
                self,
                "Weekly Retrospective",
                "No items were completed in the past 7 days.",
            )
            return

        by_scenario: dict[str, list[str]] = {}
        by_type: dict[str, int] = {}
        for scenario_name, title, type_name in recent_data:
            if scenario_name not in by_scenario:
                by_scenario[scenario_name] = []
            by_scenario[scenario_name].append(title)
            by_type[type_name] = by_type.get(type_name, 0) + 1

        lines = [f"🎉 Completed this week: {len(recent_data)} items\n"]
        
        # Summary by type
        lines.append("By Type:")
        for type_name, count in sorted(by_type.items()):
            emoji = {"Task": "📋", "Event": "📅", "Note": "📝", "Goal": "🎯"}.get(type_name, "📋")
            lines.append(f"  {emoji} {type_name}: {count}")
        
        lines.append("\nBy Scenario:")
        for scenario, items in sorted(by_scenario.items()):
            lines.append(f"\n  📁 {scenario} ({len(items)}):")
            for title in items[:5]:  # Show up to 5 items per scenario
                lines.append(f"    ✓ {title[:40]}{'...' if len(title) > 40 else ''}")
            if len(items) > 5:
                lines.append(f"    ... and {len(items) - 5} more")

        QMessageBox.information(self, "Weekly Retrospective", "\n".join(lines))

    def _add_new_item(self) -> None:
        """Open dialog to create a new item from the Plan page."""
        from src.ui.pages.todos import NewItemDialog
        from src.database.models import ItemStatus
        dialog = NewItemDialog(ItemStatus.TODO, self)
        if dialog.exec():
            self._refresh_current()
