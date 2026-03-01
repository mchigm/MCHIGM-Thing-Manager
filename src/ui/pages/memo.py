"""
MEMO page — AI Copilot chat/scratchpad interface.

Phase 1: Input area + chat history placeholder (AI wired up in Phase 3).
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MemoPage(QWidget):
    """Page 3 — MEMO AI Copilot hub."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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

        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(70)
        send_btn.setStyleSheet(
            "QPushButton { background-color: #5c85d6; color: #ffffff; border-radius: 4px;"
            " padding: 6px 12px; font-size: 13px; }"
            "QPushButton:hover { background-color: #6a95e6; }"
        )
        send_btn.clicked.connect(self._send_message)
        input_row.addWidget(send_btn)

        root.addLayout(input_row)

        note = QLabel("AI integration will be connected in Phase 3.")
        note.setStyleSheet("color: #505060; font-size: 11px;")
        root.addWidget(note)

    def _send_message(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._history.append(f"<b>You:</b> {text}")
        self._history.append(
            "<i style='color:#606070;'>AI response will appear here after Phase 3 integration.</i>"
        )
        self._input.clear()
