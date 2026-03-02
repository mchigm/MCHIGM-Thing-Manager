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
from src.calendar_sync import CalendarSyncManager, CalendarProvider
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
        self._calendar_manager = CalendarSyncManager()
        self._calendar_provider_combo = None
        self._google_creds_edit = None
        self._outlook_client_id_edit = None
        self._outlook_client_secret_edit = None
        self._outlook_tenant_id_edit = None
        self._calendar_status_label = None
        self._calendar_auto_sync_cb = None
        self._calendar_sync_interval_combo = None
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
        tabs.addTab(self._build_calendar_tab(), "Calendar Sync")
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
    # Calendar Sync tab
    # ------------------------------------------------------------------
    def _build_calendar_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        intro = QLabel(
            "Sync events with Google Calendar or Microsoft Outlook. "
            "Install required packages to enable cloud calendar integration."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #808090; font-size: 11px;")
        layout.addWidget(intro)

        # Provider selection
        provider_box = QGroupBox("Calendar Provider")
        provider_form = QFormLayout(provider_box)

        self._calendar_provider_combo = QComboBox()
        self._calendar_provider_combo.addItems(["None", "Google Calendar", "Microsoft Outlook"])
        # Set current provider from settings
        current_provider = self._settings.get("calendar_provider", "none")
        if current_provider == "google":
            self._calendar_provider_combo.setCurrentIndex(1)
        elif current_provider == "outlook":
            self._calendar_provider_combo.setCurrentIndex(2)
        else:
            self._calendar_provider_combo.setCurrentIndex(0)
        self._calendar_provider_combo.currentIndexChanged.connect(self._on_calendar_provider_changed)
        provider_form.addRow("Provider:", self._calendar_provider_combo)

        self._calendar_status_label = QLabel("Not connected")
        self._calendar_status_label.setStyleSheet("color: #808090; font-size: 11px;")
        provider_form.addRow("Status:", self._calendar_status_label)

        layout.addWidget(provider_box)

        # Google Calendar settings
        google_box = QGroupBox("Google Calendar Settings")
        google_form = QFormLayout(google_box)

        google_row = QHBoxLayout()
        self._google_creds_edit = QLineEdit()
        self._google_creds_edit.setPlaceholderText("Path to credentials.json")
        self._google_creds_edit.setText(self._settings.get("google_credentials_path", ""))
        google_row.addWidget(self._google_creds_edit, stretch=1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_google_credentials)
        google_row.addWidget(browse_btn)

        google_form.addRow("Credentials:", google_row)

        hint = QLabel(
            "Get credentials.json from Google Cloud Console → APIs & Services → Credentials"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #808090; font-size: 10px;")
        google_form.addRow("", hint)

        layout.addWidget(google_box)
        self._google_settings_box = google_box

        # Outlook settings
        outlook_box = QGroupBox("Microsoft Outlook Settings")
        outlook_form = QFormLayout(outlook_box)

        self._outlook_client_id_edit = QLineEdit()
        self._outlook_client_id_edit.setPlaceholderText("Azure AD Client ID")
        self._outlook_client_id_edit.setText(self._settings.get("outlook_client_id", ""))
        outlook_form.addRow("Client ID:", self._outlook_client_id_edit)

        self._outlook_client_secret_edit = QLineEdit()
        self._outlook_client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._outlook_client_secret_edit.setPlaceholderText("Azure AD Client Secret")
        self._outlook_client_secret_edit.setText(self._settings.get("outlook_client_secret", ""))
        outlook_form.addRow("Client Secret:", self._outlook_client_secret_edit)

        self._outlook_tenant_id_edit = QLineEdit()
        self._outlook_tenant_id_edit.setPlaceholderText("Azure AD Tenant ID")
        self._outlook_tenant_id_edit.setText(self._settings.get("outlook_tenant_id", ""))
        outlook_form.addRow("Tenant ID:", self._outlook_tenant_id_edit)

        hint2 = QLabel(
            "Register an app in Azure AD → App registrations to get these values"
        )
        hint2.setWordWrap(True)
        hint2.setStyleSheet("color: #808090; font-size: 10px;")
        outlook_form.addRow("", hint2)

        layout.addWidget(outlook_box)
        self._outlook_settings_box = outlook_box

        # Sync settings
        sync_box = QGroupBox("Sync Settings")
        sync_form = QFormLayout(sync_box)

        self._calendar_auto_sync_cb = QCheckBox("Enable automatic sync")
        self._calendar_auto_sync_cb.setChecked(self._settings.get("calendar_auto_sync", True))
        sync_form.addRow("Auto Sync:", self._calendar_auto_sync_cb)

        self._calendar_sync_interval_combo = QComboBox()
        self._calendar_sync_interval_combo.addItems(["5 minutes", "15 minutes", "30 minutes", "1 hour"])
        # Set current interval
        interval = self._settings.get("calendar_sync_interval", 15)
        if interval == 5:
            self._calendar_sync_interval_combo.setCurrentIndex(0)
        elif interval == 15:
            self._calendar_sync_interval_combo.setCurrentIndex(1)
        elif interval == 30:
            self._calendar_sync_interval_combo.setCurrentIndex(2)
        elif interval == 60:
            self._calendar_sync_interval_combo.setCurrentIndex(3)
        sync_form.addRow("Sync Interval:", self._calendar_sync_interval_combo)

        layout.addWidget(sync_box)

        # Action buttons
        btn_row = QHBoxLayout()

        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self._connect_calendar)
        btn_row.addWidget(connect_btn)

        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.clicked.connect(self._disconnect_calendar)
        btn_row.addWidget(disconnect_btn)

        sync_now_btn = QPushButton("Sync Now")
        sync_now_btn.clicked.connect(self._sync_calendar_now)
        btn_row.addWidget(sync_now_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

        # Update initial visibility based on provider
        self._on_calendar_provider_changed(self._calendar_provider_combo.currentIndex())

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
        # Get calendar sync interval
        interval_idx = self._calendar_sync_interval_combo.currentIndex() if self._calendar_sync_interval_combo else 1
        interval_map = {0: 5, 1: 15, 2: 30, 3: 60}
        sync_interval = interval_map.get(interval_idx, 15)

        # Get calendar provider
        provider_idx = self._calendar_provider_combo.currentIndex() if self._calendar_provider_combo else 0
        provider_map = {0: "none", 1: "google", 2: "outlook"}
        calendar_provider = provider_map.get(provider_idx, "none")

        if self._model_edit is not None and self._api_key_edit is not None:
            save_settings(
                {
                    "ai_model": self._model_edit.text().strip(),
                    "ai_api_key": self._api_key_edit.text().strip(),
                    "mcp_server_url": (self._mcp_server_edit.text().strip() if self._mcp_server_edit else ""),
                    "mcp_status": "connected" if self._mcp_manager.connected else "disconnected",
                    # Calendar sync settings
                    "calendar_provider": calendar_provider,
                    "calendar_connected": self._calendar_manager.connected,
                    "google_credentials_path": (self._google_creds_edit.text().strip() if self._google_creds_edit else ""),
                    "outlook_client_id": (self._outlook_client_id_edit.text().strip() if self._outlook_client_id_edit else ""),
                    "outlook_client_secret": (self._outlook_client_secret_edit.text().strip() if self._outlook_client_secret_edit else ""),
                    "outlook_tenant_id": (self._outlook_tenant_id_edit.text().strip() if self._outlook_tenant_id_edit else ""),
                    "calendar_auto_sync": (self._calendar_auto_sync_cb.isChecked() if self._calendar_auto_sync_cb else True),
                    "calendar_sync_interval": sync_interval,
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

    # ------------------------------------------------------------------
    # Calendar sync helpers
    # ------------------------------------------------------------------
    def _on_calendar_provider_changed(self, index: int) -> None:
        """Show/hide provider-specific settings based on selection."""
        if hasattr(self, '_google_settings_box') and hasattr(self, '_outlook_settings_box'):
            if index == 1:  # Google Calendar
                self._google_settings_box.setVisible(True)
                self._outlook_settings_box.setVisible(False)
            elif index == 2:  # Microsoft Outlook
                self._google_settings_box.setVisible(False)
                self._outlook_settings_box.setVisible(True)
            else:  # None
                self._google_settings_box.setVisible(False)
                self._outlook_settings_box.setVisible(False)

    def _browse_google_credentials(self) -> None:
        """Open file dialog to select Google credentials JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Google Credentials File",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        if file_path and self._google_creds_edit:
            self._google_creds_edit.setText(file_path)

    def _connect_calendar(self) -> None:
        """Connect to the selected calendar provider."""
        if not self._calendar_provider_combo:
            return

        provider_idx = self._calendar_provider_combo.currentIndex()

        if provider_idx == 0:  # None
            QMessageBox.information(
                self,
                "Calendar Sync",
                "Please select a calendar provider first."
            )
            return
        elif provider_idx == 1:  # Google Calendar
            creds_path = self._google_creds_edit.text().strip() if self._google_creds_edit else ""
            result = self._calendar_manager.connect_google(creds_path)
            self._update_calendar_status(result.message)
            if result.success:
                QMessageBox.information(self, "Calendar Sync", result.message)
            else:
                QMessageBox.warning(self, "Calendar Sync", result.message)
        elif provider_idx == 2:  # Microsoft Outlook
            client_id = self._outlook_client_id_edit.text().strip() if self._outlook_client_id_edit else ""
            client_secret = self._outlook_client_secret_edit.text().strip() if self._outlook_client_secret_edit else ""
            tenant_id = self._outlook_tenant_id_edit.text().strip() if self._outlook_tenant_id_edit else ""
            result = self._calendar_manager.connect_outlook(client_id, client_secret, tenant_id)
            self._update_calendar_status(result.message)
            if result.success:
                QMessageBox.information(self, "Calendar Sync", result.message)
            else:
                QMessageBox.warning(self, "Calendar Sync", result.message)

    def _disconnect_calendar(self) -> None:
        """Disconnect from the current calendar provider."""
        result = self._calendar_manager.disconnect()
        self._update_calendar_status(result.message)
        QMessageBox.information(self, "Calendar Sync", result.message)

    def _sync_calendar_now(self) -> None:
        """Trigger an immediate calendar sync."""
        if not self._calendar_manager.connected:
            QMessageBox.warning(
                self,
                "Calendar Sync",
                "Not connected to any calendar provider. Please connect first."
            )
            return

        # In a real implementation, this would:
        # 1. Get all Items with type=EVENT from the database
        # 2. Call calendar_manager.sync_to_cloud(items)
        # 3. Call calendar_manager.sync_from_cloud()
        # 4. Show results to the user

        QMessageBox.information(
            self,
            "Calendar Sync",
            "Manual sync triggered. (Real sync implementation to be completed)\n\n"
            "This would sync all events with the connected calendar provider."
        )

    def _update_calendar_status(self, message: str) -> None:
        """Update the calendar status label."""
        if self._calendar_status_label:
            status = self._calendar_manager.get_status_text()
            self._calendar_status_label.setText(f"{status} — {message}")
