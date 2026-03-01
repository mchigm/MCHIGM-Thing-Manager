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
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsWindow(QDialog):
    """Application settings dialog."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(480, 360)
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
        root.addWidget(tabs, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
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
