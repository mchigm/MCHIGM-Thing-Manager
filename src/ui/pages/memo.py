"""
MEMO page — AI Copilot chat/scratchpad interface.

Phase 1: Input area + chat history placeholder (AI wired up in Phase 3).
"""
import html
import json
import subprocess
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QInputDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ai.memo_agent import GeneratedItem, call_memo_agent
from src.database.models import Dependency, Item, Scenario, SessionLocal, Tag
from src.i18n import tr
from src.settings_store import load_settings

_HISTORY_PATH = Path.home() / ".mchigm_thing_manager" / "memo_history.json"


def _configured_models(settings: dict) -> list[str]:
    raw = settings.get("ai_models", [])
    parsed: list[str] = []
    if isinstance(raw, list):
        parsed = [str(model).strip() for model in raw if str(model).strip()]
    elif isinstance(raw, str):
        parsed = [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]
    fallback = str(settings.get("ai_model", "")).strip()
    if not parsed and fallback:
        parsed = [fallback]
    unique: list[str] = []
    for model in parsed:
        if model not in unique:
            unique.append(model)
    return unique[:6]


class CliInstallWorker(QObject):
    """Install OpenClaw CLI in a background thread."""

    finished = pyqtSignal(bool, str)

    def run(self) -> None:
        attempts = [
            [sys.executable, "-m", "pip", "install", "openclaw-cli"],
            [sys.executable, "-m", "pip", "install", "openclaw"],
        ]
        last_error = ""
        for cmd in attempts:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.finished.emit(True, "")
                return
            last_error = (result.stderr or result.stdout or "").strip()
        self.finished.emit(False, last_error[:500])


class MemoAgentWorker(QObject):
    """Call memo AI in a background thread."""

    finished = pyqtSignal(object, str)

    def __init__(self, text: str, models: list[str], api_key: str) -> None:
        super().__init__()
        self._text = text
        self._models = models
        self._api_key = api_key

    def run(self) -> None:
        try:
            results: list[dict[str, object]] = []
            models = self._models or [""]
            for model in models:
                ai_text, items = call_memo_agent(self._text, model, self._api_key)
                results.append(
                    {
                        "model": model or "offline",
                        "ai_text": ai_text,
                        "items": items,
                    }
                )
            self.finished.emit(results, "")
        except Exception as exc:
            self.finished.emit([], str(exc))


class MemoPage(QWidget):
    """Page 3 — MEMO AI Copilot hub."""

    def __init__(self, parent: QWidget | None = None, on_items_created=None) -> None:
        super().__init__(parent)
        self._on_items_created = on_items_created
        self._chat_messages: list[dict] = []
        self._status_label: QLabel | None = None
        self._install_cli_btn: QPushButton | None = None
        self._cli_install_thread: QThread | None = None
        self._cli_install_worker: CliInstallWorker | None = None
        self._memo_thread: QThread | None = None
        self._memo_worker: MemoAgentWorker | None = None
        self._setup_ui()
        self._load_history()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Title row with status indicator
        title_row = QHBoxLayout()
        title = QLabel("MEMO — AI Copilot")
        title.setStyleSheet("color: #c8c8d8; font-size: 18px; font-weight: bold;")
        title_row.addWidget(title)
        
        title_row.addStretch()
        
        # AI status indicator
        self._status_label = QLabel()
        self._update_status_indicator()
        title_row.addWidget(self._status_label)

        self._install_cli_btn = QPushButton(tr("memo.install_cli", "Install CLI"))
        self._install_cli_btn.setStyleSheet(
            "QPushButton { background-color: #3a5a7a; color: #ffffff; border-radius: 4px;"
            " padding: 4px 10px; font-size: 11px; }"
            "QPushButton:hover { background-color: #4a6a8a; }"
        )
        self._install_cli_btn.clicked.connect(self._install_openclaw_cli)
        title_row.addWidget(self._install_cli_btn)
        
        # Clear history button
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet(
            "QPushButton { background-color: #3a3a4a; color: #c0c0d0; border-radius: 4px;"
            " padding: 4px 10px; font-size: 11px; }"
            "QPushButton:hover { background-color: #4a4a5e; }"
        )
        clear_btn.clicked.connect(self._clear_history)
        title_row.addWidget(clear_btn)
        
        root.addLayout(title_row)

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

    def _install_openclaw_cli(self) -> None:
        reply = QMessageBox.question(
            self,
            tr("memo.install_cli.title", "Install OpenClaw CLI"),
            tr("memo.install_cli.confirm", "Install OpenClaw CLI using pip now?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._cli_install_thread is not None:
            return

        if self._install_cli_btn:
            self._install_cli_btn.setEnabled(False)
            self._install_cli_btn.setText("Installing...")
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self._cli_install_thread = QThread(self)
        self._cli_install_worker = CliInstallWorker()
        self._cli_install_worker.moveToThread(self._cli_install_thread)
        self._cli_install_thread.started.connect(self._cli_install_worker.run)
        self._cli_install_worker.finished.connect(self._on_cli_install_finished)
        self._cli_install_worker.finished.connect(self._cleanup_cli_install_thread)
        self._cli_install_thread.start()

    def _cleanup_cli_install_thread(self, _ok: bool, _message: str) -> None:
        QApplication.restoreOverrideCursor()
        if self._install_cli_btn:
            self._install_cli_btn.setEnabled(True)
            self._install_cli_btn.setText(tr("memo.install_cli", "Install CLI"))
        if self._cli_install_thread is not None:
            self._cli_install_thread.quit()
            self._cli_install_thread.wait()
            self._cli_install_thread.deleteLater()
            self._cli_install_thread = None
        if self._cli_install_worker is not None:
            self._cli_install_worker.deleteLater()
            self._cli_install_worker = None

    def _on_cli_install_finished(self, ok: bool, message: str) -> None:
        if ok:
            QMessageBox.information(
                self,
                tr("memo.install_cli.title", "Install OpenClaw CLI"),
                tr("memo.install_cli.success", "OpenClaw CLI installed successfully."),
            )
            return
        QMessageBox.warning(
            self,
            tr("memo.install_cli.title", "Install OpenClaw CLI"),
            f"{tr('memo.install_cli.fail', 'OpenClaw CLI installation failed.')}\n\n{message}",
        )

    def _update_status_indicator(self) -> None:
        """Update the AI connection status indicator."""
        if not self._status_label:
            return
        settings = load_settings()
        api_key = settings.get("ai_api_key", "")
        models = _configured_models(settings)
        
        if api_key and models:
            self._status_label.setText("🟢 AI Connected")
            self._status_label.setStyleSheet("color: #5cd685; font-size: 11px;")
            if len(models) == 1:
                self._status_label.setToolTip(f"Model: {models[0]}")
            else:
                self._status_label.setToolTip(f"Models ({len(models)}): {', '.join(models)}")
        else:
            self._status_label.setText("🔴 AI Offline")
            self._status_label.setStyleSheet("color: #d65c5c; font-size: 11px;")
            self._status_label.setToolTip("Configure API key in Settings to enable AI")

    def _load_history(self) -> None:
        """Load chat history from disk."""
        if _HISTORY_PATH.exists():
            try:
                data = json.loads(_HISTORY_PATH.read_text())
                if isinstance(data, list):
                    self._chat_messages = data
                    for msg in self._chat_messages:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if role == "user":
                            self._history.append(f"<b>You:</b> {html.escape(content)}")
                        elif role == "ai":
                            self._history.append(f"<b>AI:</b> {html.escape(content)}")
                        elif role == "system":
                            self._history.append(f"<i style='color:#7ab97a;'>{html.escape(content)}</i>")
            except Exception:
                pass

    def _save_history(self) -> None:
        """Save chat history to disk."""
        try:
            _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            _HISTORY_PATH.write_text(json.dumps(self._chat_messages, indent=2))
        except Exception:
            pass

    def _clear_history(self) -> None:
        """Clear the chat history after confirmation."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the chat history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._chat_messages.clear()
            self._history.clear()
            self._save_history()

    def _send_message(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        if self._memo_thread is not None:
            return
        self._history.append(f"<b>You:</b> {html.escape(text)}")
        self._chat_messages.append({"role": "user", "content": text})
        self._input.clear()
        self._send_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        settings = load_settings()
        models = _configured_models(settings)
        self._update_status_indicator()  # Refresh status
        self._memo_thread = QThread(self)
        self._memo_worker = MemoAgentWorker(
            text,
            models,
            str(settings.get("ai_api_key", "")),
        )
        self._memo_worker.moveToThread(self._memo_thread)
        self._memo_thread.started.connect(self._memo_worker.run)
        self._memo_worker.finished.connect(self._on_memo_result)
        self._memo_worker.finished.connect(self._cleanup_memo_thread)
        self._memo_thread.start()

    def _cleanup_memo_thread(self, _results: object, _error: str) -> None:
        QApplication.restoreOverrideCursor()
        self._send_btn.setEnabled(True)
        self._save_history()
        if self._memo_thread is not None:
            self._memo_thread.quit()
            self._memo_thread.wait()
            self._memo_thread.deleteLater()
            self._memo_thread = None
        if self._memo_worker is not None:
            self._memo_worker.deleteLater()
            self._memo_worker = None

    def _on_memo_result(self, results: object, error: str) -> None:
        if error:
            error_msg = f"Error: {error[:100]}" if error else "An error occurred"
            self._history.append(f"<i style='color:#b97a7a;'>{html.escape(error_msg)}</i>")
            self._chat_messages.append({"role": "system", "content": error_msg})
            return

        candidates = [entry for entry in (results if isinstance(results, list) else []) if isinstance(entry, dict)]
        if not candidates:
            self._history.append("<i style='color:#606070;'>No AI response.</i>")
            self._chat_messages.append({"role": "system", "content": "No AI response."})
            return

        selected = candidates[0]
        if len(candidates) > 1:
            options: list[str] = []
            for idx, candidate in enumerate(candidates):
                model = str(candidate.get("model", "unknown"))
                ai_text = str(candidate.get("ai_text", "") or "")
                generated = candidate.get("items", [])
                item_count = len(generated) if isinstance(generated, list) else 0
                options.append(f"{model} ({item_count} items)")
                preview = ai_text.strip().splitlines()[0] if ai_text.strip() else "No text response."
                preview = preview[:180]
                self._history.append(
                    f"<b>Draft {idx + 1} — {html.escape(model)}:</b> {html.escape(preview)}"
                )
                self._chat_messages.append(
                    {"role": "ai", "content": f"[{model}] {preview}"}
                )

            choice, ok = QInputDialog.getItem(
                self,
                "Choose Draft",
                "Select the draft to apply as items:",
                options,
                0,
                False,
            )
            if not ok:
                self._history.append("<i style='color:#808090;'>Draft selection canceled.</i>")
                self._chat_messages.append({"role": "system", "content": "Draft selection canceled."})
                return
            selected = candidates[options.index(choice)]
            chosen_model = str(selected.get("model", "unknown"))
            selected_msg = f"Selected draft: {chosen_model}"
            self._history.append(f"<i style='color:#7ab97a;'>{html.escape(selected_msg)}</i>")
            self._chat_messages.append({"role": "system", "content": selected_msg})

        ai_text = str(selected.get("ai_text", "") or "")
        generated = selected.get("items", [])
        generated_items = generated if isinstance(generated, list) else []
        created = self._persist_items(generated_items)
        if ai_text and len(candidates) == 1:
            self._history.append(f"<b>AI:</b> {html.escape(ai_text)}")
            self._chat_messages.append({"role": "ai", "content": ai_text})
        if created:
            msg = f"Created {created} item(s) and refreshed views."
            self._history.append(f"<i style='color:#7ab97a;'>{html.escape(msg)}</i>")
            self._chat_messages.append({"role": "system", "content": msg})
            if self._on_items_created:
                self._on_items_created()
        elif not ai_text:
            self._history.append("<i style='color:#606070;'>No AI response.</i>")
            self._chat_messages.append({"role": "system", "content": "No AI response."})

    def _persist_items(self, items: list[GeneratedItem]) -> int:
        if not items:
            return 0
        with SessionLocal() as session:
            with session.begin():
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

                # Ensure items have primary keys before creating dependencies
                session.flush()

                title_map = {gen.title: db_item for gen, db_item in created}
                for gen, db_item in created:
                    for parent_title in gen.depends_on:
                        parent = title_map.get(parent_title)
                        if parent:
                            session.add(
                                Dependency(parent_id=parent.id, child_id=db_item.id)
                            )
            return len(created)
