"""
Plan page — Roadmap / Gantt view & Weekly Retrospective.

Phase 5 adds lightweight Gantt rendering, PDF export, and a real retrospective modal.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPageSize, QPainter, QPen, QPdfWriter
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import or_

from src.database.models import Item, ItemStatus, Scenario, SessionLocal, Tag
from src.ui.search_filters import parse_search_text

_STATUS_COLOR = {
    ItemStatus.BACKLOG: QColor("#4a4a5a"),
    ItemStatus.TODO: QColor("#3a5a7a"),
    ItemStatus.DOING: QColor("#5a4a7a"),
    ItemStatus.DONE: QColor("#3a6a4a"),
}
_ROW_HEIGHT = 34
_PADDING = 24
_DAY_WIDTH = 120


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

        export_btn = QPushButton("Export PDF")
        export_btn.setStyleSheet(
            "QPushButton { background-color: #3a5a7a; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; font-size: 12px; }"
            "QPushButton:hover { background-color: #4a6a8a; }"
        )
        export_btn.clicked.connect(self._export_pdf)
        title_row.addWidget(export_btn)

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

        root.addWidget(self._view, stretch=1)

    def refresh_items(self, scenario_name: str = "All", search_text: str = "") -> None:
        """Reload items and redraw the roadmap."""
        items = self._query_items(scenario_name, search_text)
        self._render_gantt(items)

    def _query_items(self, scenario_name: str, search_text: str) -> list[Item]:
        filters = parse_search_text(search_text)
        with SessionLocal() as session:
            query = session.query(Item).outerjoin(Scenario)
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

        start_dates = []
        end_dates = []
        for item in items:
            start, end = self._time_window(item)
            start_dates.append(start)
            end_dates.append(end)
        baseline = min(start_dates) if start_dates else datetime.now(timezone.utc)
        positions: dict[int, tuple[float, float, float]] = {}
        pen = QPen(QColor("#2e2e42"))

        for idx, item in enumerate(items):
            start, end = self._time_window(item)
            start_days = max(0.0, (start - baseline).total_seconds() / 86400)
            end_days = max(start_days + 0.01, (end - baseline).total_seconds() / 86400)
            x = _PADDING + start_days * _DAY_WIDTH
            width = max(60.0, (end_days - start_days) * _DAY_WIDTH)
            y = _PADDING + idx * _ROW_HEIGHT
            color = _STATUS_COLOR.get(item.status, QColor("#3c3c50"))

            rect = self._scene.addRect(x, y, width, 18, pen, color)
            rect.setToolTip(
                f"{item.title}\nStatus: {item.status.value}\nType: {item.type.value}"
            )
            label = self._scene.addText(item.title)
            label.setDefaultTextColor(Qt.GlobalColor.white)
            label.setPos(x + 4, y - 2)
            positions[item.id] = (x, y, width)

        dep_pen = QPen(QColor("#a0a0c0"))
        dep_pen.setWidth(2)
        for item in items:
            if item.id not in positions:
                continue
            child_pos = positions[item.id]
            child_y = child_pos[1] + 9
            child_x = child_pos[0]
            for link in item.parent_links:
                parent = link.parent
                if parent and parent.id in positions:
                    px, py, pw = positions[parent.id]
                    self._scene.addLine(px + pw, py + 9, child_x, child_y, dep_pen)

        self._fit_scene()

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

    def _fit_scene(self) -> None:
        rect = self._scene.itemsBoundingRect()
        padded = rect.adjusted(-_PADDING, -_PADDING, _PADDING, _PADDING)
        if padded.isValid():
            self._view.fitInView(padded, Qt.AspectRatioMode.KeepAspectRatio)

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
        with SessionLocal() as session:
            recent = (
                session.query(Item)
                .filter(Item.status == ItemStatus.DONE, Item.updated_at >= week_ago)
                .all()
            )

        if not recent:
            QMessageBox.information(
                self,
                "Weekly Retrospective",
                "No items were completed in the past 7 days.",
            )
            return

        by_scenario: dict[str, int] = {}
        for item in recent:
            name = item.scenario.name if item.scenario else "Unassigned"
            by_scenario[name] = by_scenario.get(name, 0) + 1

        lines = [f"Completed this week: {len(recent)} items"]
        for scenario, count in sorted(by_scenario.items()):
            lines.append(f"- {scenario}: {count}")
        lines.append("\nTracker time will be included once time entries are persisted.")

        QMessageBox.information(self, "Weekly Retrospective", "\n".join(lines))
