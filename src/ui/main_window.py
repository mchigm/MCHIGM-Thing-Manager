"""
Main application window for MCHIGM Thing Manager.

Provides:
- A left navigation bar with buttons for the 4 pages.
- A Global Scenario (Workspace) dropdown in the top bar.
- An Omni-Search bar.
- A Settings button.
- Platform-aware window decorations.
- Hotkeys for navigation and quick capture.
"""
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.database.models import Item, ItemStatus, ItemType, Scenario, SessionLocal
from src.ui.pages.memo import MemoPage
from src.ui.pages.plan import PlanPage
from src.ui.pages.timetable import TimetablePage
from src.ui.pages.todos import TodosPage
from src.ui.settings_window import SettingsWindow

# ---------------------------------------------------------------------------
# Stylesheet constants
# ---------------------------------------------------------------------------
_APP_STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #c8c8d8;
}
QScrollBar:vertical {
    background: #2a2a3a;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #4a4a5e;
    border-radius: 4px;
}
QToolTip {
    background-color: #3a3a4a;
    color: #e0e0f0;
    border: 1px solid #5c85d6;
}
"""

_NAV_BTN_STYLE = """
QPushButton {{
    background-color: {bg};
    color: #c8c8d8;
    border: none;
    border-radius: 6px;
    padding: 10px 6px;
    font-size: 13px;
    text-align: left;
}}
QPushButton:hover {{
    background-color: #3a3a55;
}}
"""

_NAV_BTN_ACTIVE_BG = "#3a3a55"
_NAV_BTN_INACTIVE_BG = "transparent"


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MCHIGM Thing Manager")
        self.setMinimumSize(900, 620)
        self._page_buttons: list[QPushButton] = []
        self._shortcuts: list[QShortcut] = []
        self._setup_platform_decorations()
        self._setup_ui()
        self._register_shortcuts()
        self._load_scenarios()

    # ------------------------------------------------------------------
    # Platform-specific decorations
    # ------------------------------------------------------------------
    def _setup_platform_decorations(self) -> None:
        """Apply platform-specific window hints."""
        if sys.platform == "darwin":
            # macOS: use native title bar merged with content
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        # Windows / Linux: standard frame is fine; future phases can add custom chrome.

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        main_layout.addWidget(self._build_top_bar())

        # Content area: nav sidebar + stacked pages
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        content.addWidget(self._build_nav_bar())
        content.addWidget(self._build_pages(), stretch=1)

        content_widget = QWidget()
        content_widget.setLayout(content)
        main_layout.addWidget(content_widget, stretch=1)

    def _register_shortcuts(self) -> None:
        """Set up navigation and quick capture shortcuts."""
        for i in range(4):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            shortcut.activated.connect(lambda idx=i: self._navigate_to(idx))
            self._shortcuts.append(shortcut)

        quick_capture = QShortcut(QKeySequence("Ctrl+Space"), self)
        quick_capture.activated.connect(self._open_quick_capture)
        self._shortcuts.append(quick_capture)

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet("background-color: #12121e; border-bottom: 1px solid #2e2e42;")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # App name
        app_label = QLabel("🗂 Thing Manager")
        app_label.setStyleSheet("color: #5c85d6; font-size: 15px; font-weight: bold;")
        layout.addWidget(app_label)

        layout.addSpacing(16)

        # Global Workspace dropdown
        ws_label = QLabel("Workspace:")
        ws_label.setStyleSheet("color: #808090; font-size: 12px;")
        layout.addWidget(ws_label)

        self._scenario_combo = QComboBox()
        self._scenario_combo.setMinimumWidth(130)
        self._scenario_combo.setStyleSheet(
            "QComboBox { background-color: #2a2a3a; color: #c8c8d8; border-radius: 4px;"
            " padding: 4px 8px; border: 1px solid #3a3a4e; font-size: 12px; }"
            "QComboBox::drop-down { border: none; }"
            "QComboBox QAbstractItemView { background-color: #2a2a3a; color: #c8c8d8;"
            " selection-background-color: #5c85d6; }"
        )
        self._scenario_combo.currentTextChanged.connect(self._on_scenario_changed)
        layout.addWidget(self._scenario_combo)

        layout.addSpacing(8)

        # Omni-Search bar
        self._search_bar = QLineEdit()
        self._search_bar.setPlaceholderText("Search items, #tags, natural language…")
        self._search_bar.setMinimumWidth(240)
        self._search_bar.setMaximumWidth(400)
        self._search_bar.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0f0; border-radius: 4px;"
            "padding: 4px 10px; border: 1px solid #3a3a4e; font-size: 12px;"
        )
        self._search_bar.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self._search_bar)

        layout.addStretch()

        # Settings button
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setStyleSheet(
            "QPushButton { background-color: #2a2a3a; color: #c8c8d8; border-radius: 4px;"
            " padding: 4px 12px; border: 1px solid #3a3a4e; font-size: 12px; }"
            "QPushButton:hover { background-color: #3a3a4e; }"
        )
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        return bar

    def _build_nav_bar(self) -> QWidget:
        nav = QWidget()
        nav.setFixedWidth(160)
        nav.setStyleSheet("background-color: #12121e; border-right: 1px solid #2e2e42;")

        layout = QVBoxLayout(nav)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        pages = [
            ("✅  TODOs", 0),
            ("📅  Timetable", 1),
            ("💬  MEMO", 2),
            ("🗺   Plan", 3),
        ]

        for label, index in pages:
            btn = QPushButton(label)
            btn.setCheckable(False)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(_NAV_BTN_STYLE.format(bg=_NAV_BTN_INACTIVE_BG))
            btn.clicked.connect(lambda checked, i=index: self._navigate_to(i))
            layout.addWidget(btn)
            self._page_buttons.append(btn)

        layout.addStretch()
        return nav

    def _build_pages(self) -> QStackedWidget:
        self._stack = QStackedWidget()
        self._todos_page = TodosPage()
        self._timetable_page = TimetablePage()
        self._memo_page = MemoPage(on_items_created=self._refresh_pages)
        self._plan_page = PlanPage()

        self._stack.addWidget(self._todos_page)
        self._stack.addWidget(self._timetable_page)
        self._stack.addWidget(self._memo_page)
        self._stack.addWidget(self._plan_page)
        self._navigate_to(0)
        return self._stack

    # ------------------------------------------------------------------
    # Scenario management
    # ------------------------------------------------------------------
    def _load_scenarios(self) -> None:
        """Populate the Workspace dropdown from the database."""
        self._scenario_combo.blockSignals(True)
        self._scenario_combo.clear()
        self._scenario_combo.addItem("All")

        with SessionLocal() as session:
            scenarios = session.query(Scenario).order_by(Scenario.name).all()
            for s in scenarios:
                self._scenario_combo.addItem(s.name)

        # Seed default scenarios if the DB is empty
        if self._scenario_combo.count() == 1:
            self._seed_default_scenarios()

        self._scenario_combo.blockSignals(False)
        self._on_scenario_changed(self._scenario_combo.currentText())

    def _seed_default_scenarios(self) -> None:
        """Insert default scenarios on first run."""
        defaults = [
            Scenario(name="School", color="#5c85d6"),
            Scenario(name="Work", color="#d6855c"),
            Scenario(name="Personal", color="#5cd685"),
        ]
        with SessionLocal() as session:
            session.add_all(defaults)
            session.commit()
        self._load_scenarios()

    def _on_scenario_changed(self, name: str) -> None:
        self._refresh_pages()

    def _on_search_text_changed(self, _: str) -> None:
        self._refresh_pages()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _navigate_to(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._page_buttons):
            bg = _NAV_BTN_ACTIVE_BG if i == index else _NAV_BTN_INACTIVE_BG
            btn.setStyleSheet(_NAV_BTN_STYLE.format(bg=bg))

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def _open_settings(self) -> None:
        dlg = SettingsWindow(self)
        dlg.exec()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _refresh_pages(self) -> None:
        scenario = self._scenario_combo.currentText()
        search = self._search_bar.text()
        self._todos_page.refresh_items(scenario, search)
        self._timetable_page.refresh_items(scenario, search)
        self._plan_page.refresh_items(scenario, search)

    def _open_quick_capture(self) -> None:
        """Capture a memo/task straight into Backlog (Ctrl+Space)."""
        text, ok = QInputDialog.getText(self, "Quick Capture", "Memo or task title:")
        if not ok or not text.strip():
            return

        with SessionLocal() as session:
            scenario_obj = None
            current = self._scenario_combo.currentText()
            if current != "All":
                scenario_obj = session.query(Scenario).filter(Scenario.name == current).first()
            item = Item(
                title=text.strip()[:255],
                description="Captured via quick shortcut (Ctrl+Space).",
                type=ItemType.NOTE,
                status=ItemStatus.BACKLOG,
                scenario=scenario_obj,
            )
            session.add(item)
            session.commit()

        QMessageBox.information(self, "Saved", "Captured to Backlog.")
        self._refresh_pages()
