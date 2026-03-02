"""
MEMO page — AI Copilot chat/scratchpad interface.

Phase 1: Input area + chat history placeholder (AI wired up in Phase 3).
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ai.memo_agent import GeneratedItem, call_memo_agent
from src.database.models import Dependency, Item, Scenario, SessionLocal, Tag
from src.settings_store import load_settings


class MemoPage(QWidget):
    """Page 3 — MEMO AI Copilot hub."""

    def __init__(self, parent: QWidget | None = None, on_items_created=None) -> None:
        super().__init__(parent)
        self._on_items_created = on_items_created
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("MEMO — AI Copilot")
        title.setStyleSheet("color: #c8c8d8; font-size: 18px; font-weight: bold;")
        root.addWidget(title)

        # Chat history area
        self._history = QTextEdit()
        self._history.setReadOnly(True)
        self._history.setStyleSheet(
            "background-color: #1e1e2e; color: #c8c8d8; border-radius: 6px;"
            "padding: 8px; font-size: 13px; border: 1px solid #3a3a4a;"
        )
        self._history.setPlaceholderText(
            "Your conversation with the AI will appear here.\n\n"
            "Example: \"Got an assignment for CS 101 due next Friday, "
            "need to start researching tomorrow.\""
        )
        root.addWidget(self._history, stretch=1)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a memo or ask the AI…")
        self._input.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0f0; border-radius: 4px;"
            "padding: 6px 10px; border: 1px solid #4a4a5e; font-size: 13px;"
        )
        self._input.returnPressed.connect(self._send_message)
        input_row.addWidget(self._input, stretch=1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedWidth(70)
        self._send_btn.setStyleSheet(
            "QPushButton { background-color: #5c85d6; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; font-size: 13px; }"
            "QPushButton:hover { background-color: #6a95e6; }"
        )
        self._send_btn.clicked.connect(self._send_message)
        input_row.addWidget(self._send_btn)

        root.addLayout(input_row)

        note = QLabel(
            "The AI will turn memos into structured Items (Task/Event/Note/Goal). "
            "Without an API key it saves a Note in Backlog."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #505060; font-size: 11px;")
        root.addWidget(note)

    def _send_message(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._history.append(f"<b>You:</b> {text}")
        self._input.clear()
        self._send_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        QApplication.processEvents()

        settings = load_settings()
        ai_text, items = call_memo_agent(
            text, settings.get("ai_model", ""), settings.get("ai_api_key", "")
        )

        created = self._persist_items(items)
        if ai_text:
            self._history.append(f"<b>AI:</b> {ai_text}")
        if created:
            self._history.append(
                f"<i style='color:#7ab97a;'>Created {created} item(s) and refreshed views.</i>"
            )
            if self._on_items_created:
                self._on_items_created()
        elif not ai_text:
            self._history.append("<i style='color:#606070;'>No AI response.</i>")

        QApplication.restoreOverrideCursor()
        self._send_btn.setEnabled(True)

    def _persist_items(self, items: list[GeneratedItem]) -> int:
        if not items:
            return 0
        with SessionLocal() as session:
            scenarios = {s.name: s for s in session.query(Scenario).all()}
            tags = {t.name: t for t in session.query(Tag).all()}
            created: list[tuple[GeneratedItem, Item]] = []

            for gen in items:
                scenario = None
                if gen.scenario:
                    scenario = scenarios.get(gen.scenario)
                    if scenario is None:
                        scenario = Scenario(name=gen.scenario)
                        session.add(scenario)
                        session.flush()
                        scenarios[gen.scenario] = scenario

                db_item = Item(
                    title=gen.title,
                    description=gen.description,
                    type=gen.type,
                    status=gen.status,
                    start_time=gen.start_time,
                    end_time=gen.end_time,
                    deadline=gen.deadline,
                    scenario=scenario,
                )

                db_tags = []
                for tag_name in gen.tags:
                    tag = tags.get(tag_name)
                    if tag is None:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                        session.flush()
                        tags[tag_name] = tag
                    db_tags.append(tag)
                db_item.tags = db_tags

                session.add(db_item)
                created.append((gen, db_item))

            session.commit()

            title_map = {gen.title: db_item for gen, db_item in created}
            for gen, db_item in created:
                for parent_title in gen.depends_on:
                    parent = title_map.get(parent_title)
                    if parent:
                        session.add(Dependency(parent_id=parent.id, child_id=db_item.id))
            session.commit()
            return len(created)
