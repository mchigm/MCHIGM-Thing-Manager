"""
Settings window — General and Data Management tabs.

Phase 1: General (theme, default scenario, notifications) and
         Data (backup/restore) tabs.
"""
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.mcp_client import MCPClientManager
from src.settings_store import load_settings, save_settings


class SettingsWindow(QDialog):
    """Application settings dialog."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(480, 360)
        self._settings = load_settings()
        self._model_edit = None
        self._api_key_edit = None
        self._mcp_manager = MCPClientManager()
        self._mcp_server_edit = None
        self._mcp_status_label = None
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_data_tab(), "Data Management")
        tabs.addTab(self._build_ai_tab(), "AI Agent")
        tabs.addTab(self._build_mcp_tab(), "MCP Client")
        root.addWidget(tabs, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close
        )
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    # ------------------------------------------------------------------
    # General tab
    # ------------------------------------------------------------------
    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Appearance
        appearance_box = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance_box)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        appearance_form.addRow("Theme:", self._theme_combo)

        layout.addWidget(appearance_box)

        # Workspace
        workspace_box = QGroupBox("Workspace")
        workspace_form = QFormLayout(workspace_box)

        self._default_scenario_combo = QComboBox()
        self._default_scenario_combo.addItems(["All", "School", "Work", "Personal"])
        workspace_form.addRow("Default Workspace:", self._default_scenario_combo)

        layout.addWidget(workspace_box)

        # Notifications
        notif_box = QGroupBox("Notifications")
        notif_layout = QVBoxLayout(notif_box)
        self._notif_deadline_cb = QCheckBox("Notify on upcoming deadlines")
        self._notif_deadline_cb.setChecked(True)
        notif_layout.addWidget(self._notif_deadline_cb)

        layout.addWidget(notif_box)
        layout.addStretch()
        return tab

    # ------------------------------------------------------------------
    # Data Management tab
    # ------------------------------------------------------------------
    def _build_data_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        backup_box = QGroupBox("Backup & Restore")
        backup_layout = QVBoxLayout(backup_box)

        db_path_label = QLabel(f"Database: {self._db_path()}")
        db_path_label.setWordWrap(True)
        db_path_label.setStyleSheet("color: #808090; font-size: 11px;")
        backup_layout.addWidget(db_path_label)

        btn_row = QHBoxLayout()

        backup_btn = QPushButton("Backup Database…")
        backup_btn.clicked.connect(self._backup_db)
        btn_row.addWidget(backup_btn)

        restore_btn = QPushButton("Restore Database…")
        restore_btn.clicked.connect(self._restore_db)
        btn_row.addWidget(restore_btn)

        backup_layout.addLayout(btn_row)
        layout.addWidget(backup_box)
        layout.addStretch()
        return tab

    # ------------------------------------------------------------------
    # AI tab
    # ------------------------------------------------------------------
    def _build_ai_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        model_box = QGroupBox("Model Selection")
        model_form = QFormLayout(model_box)

        self._model_edit = QLineEdit()
        self._model_edit.setPlaceholderText("e.g., gpt-4o-mini, claude-3-haiku")
        self._model_edit.setText(self._settings.get("ai_model", ""))
        model_form.addRow("Model:", self._model_edit)
        layout.addWidget(model_box)

        creds_box = QGroupBox("Credentials")
        creds_form = QFormLayout(creds_box)

        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setPlaceholderText("API key (stored locally)")
        self._api_key_edit.setText(self._settings.get("ai_api_key", ""))
        creds_form.addRow("API Key:", self._api_key_edit)
        layout.addWidget(creds_box)

        hint = QLabel(
            "AI is optional. Without a key, MEMO will save notes locally without calling a model."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #808090; font-size: 11px;")
        layout.addWidget(hint)
        layout.addStretch()
        return tab

    # ------------------------------------------------------------------
    # MCP Client tab
    # ------------------------------------------------------------------
    def _build_mcp_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        intro = QLabel(
            "Connect to external MCP servers (e.g., Craft, Teams) so the AI copilot can "
            "read/write data. Install the official 'mcp[cli]' package to enable live connections."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #808090; font-size: 11px;")
        layout.addWidget(intro)

        form_box = QGroupBox("Connection")
        form = QFormLayout(form_box)

        self._mcp_server_edit = QLineEdit()
        self._mcp_server_edit.setPlaceholderText("mcp://localhost:8000 or https://server")
        self._mcp_server_edit.setText(self._settings.get("mcp_server_url", ""))
        form.addRow("Server URL:", self._mcp_server_edit)

        mcp_status_text = "connected" if getattr(self._mcp_manager, "connected", False) else "disconnected"
        self._mcp_status_label = QLabel(mcp_status_text)
        self._mcp_status_label.setStyleSheet("color: #808090; font-size: 11px;")
        form.addRow("Status:", self._mcp_status_label)

        btn_row = QHBoxLayout()
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self._connect_mcp)
        btn_row.addWidget(connect_btn)

        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.clicked.connect(self._disconnect_mcp)
        btn_row.addWidget(disconnect_btn)

        btn_row.addStretch()
        form.addRow(btn_row)

        layout.addWidget(form_box)
        layout.addStretch()
        return tab

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _db_path() -> Path:
        return Path.home() / ".mchigm_thing_manager" / "things.db"

    def _backup_db(self) -> None:
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save Backup", str(Path.home() / "things_backup.db"), "SQLite DB (*.db)"
        )
        if dest:
            try:
                shutil.copy2(self._db_path(), dest)
                QMessageBox.information(self, "Backup", "Database backed up successfully.")
            except Exception as exc:
                QMessageBox.critical(self, "Backup Failed", str(exc))

    def _restore_db(self) -> None:
        src, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", str(Path.home()), "SQLite DB (*.db)"
        )
        if src:
            reply = QMessageBox.question(
                self,
                "Restore Database",
                "This will overwrite the current database. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    shutil.copy2(src, self._db_path())
                    QMessageBox.information(
                        self,
                        "Restore",
                        "Database restored. Please restart the application.",
                    )
                except Exception as exc:
                    QMessageBox.critical(self, "Restore Failed", str(exc))

    def _save_and_close(self) -> None:
        if self._model_edit is not None and self._api_key_edit is not None:
            save_settings(
                {
                    "ai_model": self._model_edit.text().strip(),
                    "ai_api_key": self._api_key_edit.text().strip(),
                    "mcp_server_url": (self._mcp_server_edit.text().strip() if self._mcp_server_edit else ""),
                    "mcp_status": "connected" if self._mcp_manager.connected else "disconnected",
                }
            )
        self.accept()

    # ------------------------------------------------------------------
    # MCP helpers
    # ------------------------------------------------------------------
    def _connect_mcp(self) -> None:
        url = self._mcp_server_edit.text().strip() if self._mcp_server_edit else ""
        result = self._mcp_manager.connect(url)
        self._update_mcp_status(result.message)

    def _disconnect_mcp(self) -> None:
        result = self._mcp_manager.disconnect()
        self._update_mcp_status(result.message)

    def _update_mcp_status(self, message: str) -> None:
        if self._mcp_status_label:
            status = "connected" if self._mcp_manager.connected else "disconnected"
            self._mcp_status_label.setText(f"{status} — {message}")
