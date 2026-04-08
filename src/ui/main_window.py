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
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.database.models import Item, ItemStatus, ItemType, Scenario, SessionLocal, Tag
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
        self._set_app_icon()
        self._page_buttons: list[QPushButton] = []
        self._shortcuts: list[QShortcut] = []
        self._active_filters: dict = {}
        self._setup_platform_decorations()
        self._setup_ui()
        self._register_shortcuts()
        self._load_scenarios()

    def _set_app_icon(self) -> None:
        """Set the application window icon."""
        # Try multiple locations for the icon
        icon_paths = [
            Path(__file__).parent.parent.parent / "icon.png",  # project root
            Path(__file__).parent / "icon.png",
            Path.cwd() / "icon.png",
        ]
        for icon_path in icon_paths:
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                # Also set for the application
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(QIcon(str(icon_path)))
                break

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
        
        # Filter panel (hidden by default)
        self._filter_panel = self._build_filter_panel()
        self._filter_panel.setVisible(False)
        main_layout.addWidget(self._filter_panel)

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

        # Filter button
        self._filter_btn = QPushButton("🔍 Filters")
        self._filter_btn.setCheckable(True)
        self._filter_btn.setStyleSheet(
            "QPushButton { background-color: #2a2a3a; color: #c8c8d8; border-radius: 4px;"
            " padding: 4px 12px; border: 1px solid #3a3a4e; font-size: 12px; }"
            "QPushButton:hover { background-color: #3a3a4e; }"
            "QPushButton:checked { background-color: #3a5a7a; border-color: #5c85d6; }"
        )
        self._filter_btn.clicked.connect(self._toggle_filter_panel)
        layout.addWidget(self._filter_btn)

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

    def _build_filter_panel(self) -> QWidget:
        """Build the advanced filter panel."""
        from PyQt6.QtWidgets import QSpinBox, QCheckBox
        
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a2e; border-bottom: 1px solid #2e2e42;")
        panel.setFixedHeight(60)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)
        
        # Tags filter
        tags_label = QLabel("Tags:")
        tags_label.setStyleSheet("color: #808090; font-size: 12px;")
        layout.addWidget(tags_label)
        
        self._tags_filter = QComboBox()
        self._tags_filter.addItem("All Tags")
        with SessionLocal() as session:
            tags = session.query(Tag).order_by(Tag.name).all()
            for tag in tags:
                self._tags_filter.addItem(tag.name)
        self._tags_filter.setStyleSheet(
            "QComboBox { background-color: #2a2a3a; color: #c8c8d8; border-radius: 4px;"
            " padding: 4px 8px; border: 1px solid #3a3a4e; font-size: 11px; min-width: 100px; }"
        )
        self._tags_filter.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self._tags_filter)
        
        # Workload filter
        workload_label = QLabel("Workload:")
        workload_label.setStyleSheet("color: #808090; font-size: 12px;")
        layout.addWidget(workload_label)
        
        self._workload_min = QSpinBox()
        self._workload_min.setRange(0, 5)
        self._workload_min.setSpecialValueText("Any")
        self._workload_min.setStyleSheet(
            "background-color: #2a2a3a; color: #c8c8d8; border-radius: 4px;"
            "border: 1px solid #3a3a4e; padding: 2px;"
        )
        self._workload_min.valueChanged.connect(self._apply_filters)
        layout.addWidget(self._workload_min)
        
        to_label = QLabel("to")
        to_label.setStyleSheet("color: #606070; font-size: 11px;")
        layout.addWidget(to_label)
        
        self._workload_max = QSpinBox()
        self._workload_max.setRange(0, 5)
        self._workload_max.setValue(5)
        self._workload_max.setSpecialValueText("Any")
        self._workload_max.setStyleSheet(
            "background-color: #2a2a3a; color: #c8c8d8; border-radius: 4px;"
            "border: 1px solid #3a3a4e; padding: 2px;"
        )
        self._workload_max.valueChanged.connect(self._apply_filters)
        layout.addWidget(self._workload_max)
        
        # Estimated time filter
        time_label = QLabel("Est. Time:")
        time_label.setStyleSheet("color: #808090; font-size: 12px;")
        layout.addWidget(time_label)
        
        self._time_min = QSpinBox()
        self._time_min.setRange(0, 999)
        self._time_min.setSuffix(" min")
        self._time_min.setSpecialValueText("Any")
        self._time_min.setStyleSheet(
            "background-color: #2a2a3a; color: #c8c8d8; border-radius: 4px;"
            "border: 1px solid #3a3a4e; padding: 2px;"
        )
        self._time_min.valueChanged.connect(self._apply_filters)
        layout.addWidget(self._time_min)
        
        to_label2 = QLabel("to")
        to_label2.setStyleSheet("color: #606070; font-size: 11px;")
        layout.addWidget(to_label2)
        
        self._time_max = QSpinBox()
        self._time_max.setRange(0, 999)
        self._time_max.setValue(999)
        self._time_max.setSuffix(" min")
        self._time_max.setSpecialValueText("Any")
        self._time_max.setStyleSheet(
            "background-color: #2a2a3a; color: #c8c8d8; border-radius: 4px;"
            "border: 1px solid #3a3a4e; padding: 2px;"
        )
        self._time_max.valueChanged.connect(self._apply_filters)
        layout.addWidget(self._time_max)
        
        # Has workload checkbox
        self._has_workload_cb = QCheckBox("Has workload")
        self._has_workload_cb.setStyleSheet("color: #c8c8d8; font-size: 11px;")
        self._has_workload_cb.stateChanged.connect(self._apply_filters)
        layout.addWidget(self._has_workload_cb)
        
        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet(
            "QPushButton { background-color: #3a3a4e; color: #c8c8d8; border-radius: 4px;"
            " padding: 4px 8px; font-size: 11px; }"
            "QPushButton:hover { background-color: #4a4a5e; }"
        )
        reset_btn.clicked.connect(self._reset_filters)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        return panel

    def _toggle_filter_panel(self) -> None:
        """Show/hide the filter panel."""
        self._filter_panel.setVisible(self._filter_btn.isChecked())
    
    def _reset_filters(self) -> None:
        """Reset all filters to default."""
        self._tags_filter.setCurrentIndex(0)
        self._workload_min.setValue(0)
        self._workload_max.setValue(5)
        self._time_min.setValue(0)
        self._time_max.setValue(999)
        self._has_workload_cb.setChecked(False)
        self._apply_filters()
    
    def _apply_filters(self) -> None:
        """Apply advanced filters to the search."""
        # Build a filter string that can be parsed by the search system
        filters = []
        
        tag = self._tags_filter.currentText()
        if tag != "All Tags":
            filters.append(tag)
        
        # Store filter state for pages to use
        self._active_filters = {
            'tag': tag if tag != "All Tags" else None,
            'workload_min': self._workload_min.value() if self._workload_min.value() > 0 else None,
            'workload_max': self._workload_max.value() if self._workload_max.value() < 5 else None,
            'time_min': self._time_min.value() if self._time_min.value() > 0 else None,
            'time_max': self._time_max.value() if self._time_max.value() < 999 else None,
            'has_workload': self._has_workload_cb.isChecked(),
        }
        
        # Refresh pages with current filters
        self._refresh_pages()

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
        """Capture a memo/task with type and scenario selection (Ctrl+Space)."""
        dialog = QuickCaptureDialog(self._scenario_combo.currentText(), self)
        if dialog.exec():
            self._refresh_pages()


class QuickCaptureDialog(QDialog):
    """Enhanced quick capture dialog with type and scenario selection."""

    def __init__(self, current_scenario: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._current_scenario = current_scenario
        self.setWindowTitle("Quick Capture (Ctrl+Space)")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        from PyQt6.QtWidgets import QFormLayout, QDialogButtonBox, QComboBox, QLineEdit, QTextEdit
        
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("What's on your mind?")
        self.title_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 8px; font-size: 14px;"
        )
        form.addRow("Title:", self.title_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Optional details...")
        self.description_edit.setStyleSheet(
            "background-color: #2a2a3a; color: #e0e0e0; border: 1px solid #3a3a4e;"
            "border-radius: 4px; padding: 4px;"
        )
        self.description_edit.setMaximumHeight(80)
        form.addRow("Details:", self.description_edit)

        # Type selector
        self.type_combo = QComboBox()
        for item_type in ItemType:
            emoji = {"Task": "📋", "Event": "📅", "Note": "📝", "Goal": "🎯"}.get(item_type.value, "📋")
            self.type_combo.addItem(f"{emoji} {item_type.value}", item_type)
        self.type_combo.setCurrentIndex(0)  # Default to Task
        form.addRow("Type:", self.type_combo)

        # Status selector
        self.status_combo = QComboBox()
        for status in ItemStatus:
            self.status_combo.addItem(status.value, status)
        self.status_combo.setCurrentIndex(0)  # Default to Backlog
        form.addRow("Status:", self.status_combo)

        # Scenario selector
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItem("None")
        with SessionLocal() as session:
            scenarios = session.query(Scenario).order_by(Scenario.name).all()
            for s in scenarios:
                self.scenario_combo.addItem(s.name)
        # Set current scenario if not "All"
        if self._current_scenario != "All":
            idx = self.scenario_combo.findText(self._current_scenario)
            if idx >= 0:
                self.scenario_combo.setCurrentIndex(idx)
        form.addRow("Scenario:", self.scenario_combo)

        layout.addLayout(form)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_item)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus on title
        self.title_edit.setFocus()

    def _save_item(self):
        """Save the captured item."""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Required", "Please enter a title.")
            return

        with SessionLocal() as session:
            scenario = None
            scenario_name = self.scenario_combo.currentText()
            if scenario_name != "None":
                scenario = session.query(Scenario).filter(Scenario.name == scenario_name).first()

            item = Item(
                title=title[:255],
                description=self.description_edit.toPlainText().strip() or "Captured via quick shortcut (Ctrl+Space).",
                type=self.type_combo.currentData(),
                status=self.status_combo.currentData(),
                scenario=scenario,
            )
            session.add(item)
            session.commit()

        self.accept()
