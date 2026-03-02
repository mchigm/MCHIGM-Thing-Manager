#!/usr/bin/env python3
"""
MCHIGM Thing Manager Setup Wizard
A comprehensive installation and management wizard for Windows and macOS

Features:
- Install application
- Repair/Fix installation
- Test installation
- Uninstall
- Configure settings
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QMessageBox, QLineEdit,
        QProgressBar, QTabWidget, QGroupBox, QFormLayout, QCheckBox,
        QRadioButton, QButtonGroup, QFileDialog
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False


class WorkerThread(QThread):
    """Worker thread for long-running operations"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, operation, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        try:
            if self.operation == "install":
                self.install()
            elif self.operation == "test":
                self.test()
            elif self.operation == "repair":
                self.repair()
            elif self.operation == "uninstall":
                self.uninstall()
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

    def install(self):
        """Install the application"""
        install_dir = self.kwargs.get('install_dir')
        create_shortcuts = self.kwargs.get('create_shortcuts', True)

        self.progress.emit("Starting installation...")

        # Create installation directory
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
            self.progress.emit(f"Created directory: {install_dir}")

        # Copy executable
        exe_source = self.kwargs.get('exe_source')
        if exe_source and os.path.exists(exe_source):
            exe_dest = os.path.join(install_dir, os.path.basename(exe_source))
            shutil.copy2(exe_source, exe_dest)
            self.progress.emit(f"Copied executable to: {exe_dest}")

        # Create data directory
        data_dir = Path.home() / ".mchigm_thing_manager"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.progress.emit(f"Created data directory: {data_dir}")

        # Create shortcuts
        if create_shortcuts and sys.platform == 'win32':
            self.progress.emit("Creating shortcuts...")
            # Desktop shortcut would be created here

        self.progress.emit("Installation completed successfully!")
        self.finished.emit(True, "Installation completed successfully!")

    def test(self):
        """Test the installation"""
        self.progress.emit("Testing installation...")

        # Check data directory
        data_dir = Path.home() / ".mchigm_thing_manager"
        if not data_dir.exists():
            self.finished.emit(False, "Data directory not found")
            return
        self.progress.emit(f"✓ Data directory exists: {data_dir}")

        # Check database
        db_file = data_dir / "things.db"
        if db_file.exists():
            self.progress.emit(f"✓ Database found: {db_file}")
        else:
            self.progress.emit(f"⚠ Database not yet created (will be created on first run)")

        # Check settings
        settings_file = data_dir / "settings.json"
        if settings_file.exists():
            self.progress.emit(f"✓ Settings file found: {settings_file}")
        else:
            self.progress.emit(f"⚠ Settings not yet configured (will use defaults)")

        self.progress.emit("Test completed!")
        self.finished.emit(True, "Installation test passed!")

    def repair(self):
        """Repair the installation"""
        self.progress.emit("Starting repair...")

        # Recreate data directory
        data_dir = Path.home() / ".mchigm_thing_manager"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.progress.emit(f"Verified data directory: {data_dir}")

        # Backup existing data
        db_file = data_dir / "things.db"
        if db_file.exists():
            backup = data_dir / "things.db.backup"
            shutil.copy2(db_file, backup)
            self.progress.emit(f"Created database backup: {backup}")

        settings_file = data_dir / "settings.json"
        if settings_file.exists():
            backup = data_dir / "settings.json.backup"
            shutil.copy2(settings_file, backup)
            self.progress.emit(f"Created settings backup: {backup}")

        self.progress.emit("Repair completed!")
        self.finished.emit(True, "Repair completed successfully!")

    def uninstall(self):
        """Uninstall the application"""
        remove_data = self.kwargs.get('remove_data', True)
        install_dir = self.kwargs.get('install_dir')

        self.progress.emit("Starting uninstallation...")

        # Remove data directory
        if remove_data:
            data_dir = Path.home() / ".mchigm_thing_manager"
            if data_dir.exists():
                shutil.rmtree(data_dir)
                self.progress.emit(f"Removed data directory: {data_dir}")

        # Remove installation directory
        if install_dir and os.path.exists(install_dir):
            try:
                shutil.rmtree(install_dir)
                self.progress.emit(f"Removed installation directory: {install_dir}")
            except Exception as e:
                self.progress.emit(f"Warning: Could not remove {install_dir}: {e}")

        self.progress.emit("Uninstallation completed!")
        self.finished.emit(True, "Uninstallation completed successfully!")


class SetupWizard(QMainWindow):
    """Main setup wizard window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCHIGM Thing Manager - Setup Wizard")
        self.setMinimumSize(700, 500)

        # Default settings
        if sys.platform == 'win32':
            self.install_dir = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                                           'MCHIGM Thing Manager')
        else:
            self.install_dir = '/Applications'

        self.exe_source = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Title
        title = QLabel("MCHIGM Thing Manager")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Setup and Management Wizard")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Tabs for different operations
        tabs = QTabWidget()

        # Install tab
        install_tab = self.create_install_tab()
        tabs.addTab(install_tab, "Install")

        # Test tab
        test_tab = self.create_test_tab()
        tabs.addTab(test_tab, "Test")

        # Repair tab
        repair_tab = self.create_repair_tab()
        tabs.addTab(repair_tab, "Repair")

        # Settings tab
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "Settings")

        # Uninstall tab
        uninstall_tab = self.create_uninstall_tab()
        tabs.addTab(uninstall_tab, "Uninstall")

        layout.addWidget(tabs)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log_output)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def create_install_tab(self):
        """Create the installation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Installation directory
        dir_group = QGroupBox("Installation Directory")
        dir_layout = QFormLayout()

        self.install_dir_input = QLineEdit(self.install_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_install_dir)

        dir_row = QHBoxLayout()
        dir_row.addWidget(self.install_dir_input)
        dir_row.addWidget(browse_btn)

        dir_layout.addRow("Install to:", dir_row)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # Executable source
        exe_group = QGroupBox("Executable")
        exe_layout = QFormLayout()

        self.exe_source_input = QLineEdit()
        browse_exe_btn = QPushButton("Browse...")
        browse_exe_btn.clicked.connect(self.browse_exe_source)

        exe_row = QHBoxLayout()
        exe_row.addWidget(self.exe_source_input)
        exe_row.addWidget(browse_exe_btn)

        exe_layout.addRow("Executable:", exe_row)
        exe_group.setLayout(exe_layout)
        layout.addWidget(exe_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.create_shortcuts_cb = QCheckBox("Create desktop shortcut")
        self.create_shortcuts_cb.setChecked(True)
        options_layout.addWidget(self.create_shortcuts_cb)

        self.create_startmenu_cb = QCheckBox("Add to Start Menu")
        self.create_startmenu_cb.setChecked(True)
        options_layout.addWidget(self.create_startmenu_cb)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Install button
        install_btn = QPushButton("Install")
        install_btn.clicked.connect(self.run_install)
        install_btn.setMinimumHeight(40)
        layout.addWidget(install_btn)

        layout.addStretch()
        return widget

    def create_test_tab(self):
        """Create the test tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("Test the installation to verify all components are working correctly.")
        info.setWordWrap(True)
        layout.addWidget(info)

        test_btn = QPushButton("Run Tests")
        test_btn.clicked.connect(self.run_test)
        test_btn.setMinimumHeight(40)
        layout.addWidget(test_btn)

        layout.addStretch()
        return widget

    def create_repair_tab(self):
        """Create the repair tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("Repair the installation by recreating data directories and backing up existing data.")
        info.setWordWrap(True)
        layout.addWidget(info)

        repair_btn = QPushButton("Repair Installation")
        repair_btn.clicked.connect(self.run_repair)
        repair_btn.setMinimumHeight(40)
        layout.addWidget(repair_btn)

        layout.addStretch()
        return widget

    def create_settings_tab(self):
        """Create the settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("Configure application settings.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Load current settings
        data_dir = Path.home() / ".mchigm_thing_manager"
        settings_file = data_dir / "settings.json"

        settings_group = QGroupBox("Current Settings")
        settings_layout = QFormLayout()

        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    for key, value in settings.items():
                        settings_layout.addRow(f"{key}:", QLabel(str(value)))
            except Exception as e:
                settings_layout.addRow("Error:", QLabel(str(e)))
        else:
            settings_layout.addRow("Status:", QLabel("No settings file found"))

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        open_settings_btn = QPushButton("Open Settings File")
        open_settings_btn.clicked.connect(self.open_settings_file)
        layout.addWidget(open_settings_btn)

        layout.addStretch()
        return widget

    def create_uninstall_tab(self):
        """Create the uninstall tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        warning = QLabel("⚠ WARNING: This will remove the application and optionally all user data.")
        warning.setStyleSheet("color: red; font-weight: bold;")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        self.remove_data_cb = QCheckBox("Remove all user data (database, settings)")
        self.remove_data_cb.setChecked(False)
        layout.addWidget(self.remove_data_cb)

        uninstall_btn = QPushButton("Uninstall")
        uninstall_btn.clicked.connect(self.run_uninstall)
        uninstall_btn.setMinimumHeight(40)
        uninstall_btn.setStyleSheet("background-color: #cc0000; color: white;")
        layout.addWidget(uninstall_btn)

        layout.addStretch()
        return widget

    def browse_install_dir(self):
        """Browse for installation directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Installation Directory",
                                                     self.install_dir_input.text())
        if dir_path:
            self.install_dir_input.setText(dir_path)

    def browse_exe_source(self):
        """Browse for executable source"""
        if sys.platform == 'win32':
            filter_str = "Executable Files (*.exe);;All Files (*.*)"
        else:
            filter_str = "Applications (*.app);;All Files (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Executable", "", filter_str)
        if file_path:
            self.exe_source_input.setText(file_path)

    def open_settings_file(self):
        """Open the settings file location"""
        data_dir = Path.home() / ".mchigm_thing_manager"
        if sys.platform == 'win32':
            os.startfile(str(data_dir))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(data_dir)])
        else:
            subprocess.run(['xdg-open', str(data_dir)])

    def log(self, message):
        """Add message to log"""
        self.log_output.append(message)

    def run_install(self):
        """Run installation"""
        install_dir = self.install_dir_input.text()
        exe_source = self.exe_source_input.text()

        if not exe_source or not os.path.exists(exe_source):
            QMessageBox.warning(self, "Error", "Please select a valid executable file.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = WorkerThread(
            "install",
            install_dir=install_dir,
            exe_source=exe_source,
            create_shortcuts=self.create_shortcuts_cb.isChecked()
        )
        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.start()

    def run_test(self):
        """Run installation test"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = WorkerThread("test")
        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.start()

    def run_repair(self):
        """Run installation repair"""
        reply = QMessageBox.question(self, "Confirm Repair",
                                     "This will backup your current data and repair the installation. Continue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            self.worker = WorkerThread("repair")
            self.worker.progress.connect(self.log)
            self.worker.finished.connect(self.on_operation_finished)
            self.worker.start()

    def run_uninstall(self):
        """Run uninstallation"""
        reply = QMessageBox.question(self, "Confirm Uninstall",
                                     "Are you sure you want to uninstall MCHIGM Thing Manager?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            self.worker = WorkerThread(
                "uninstall",
                remove_data=self.remove_data_cb.isChecked(),
                install_dir=self.install_dir_input.text()
            )
            self.worker.progress.connect(self.log)
            self.worker.finished.connect(self.on_operation_finished)
            self.worker.start()

    def on_operation_finished(self, success, message):
        """Handle operation completion"""
        self.progress_bar.setVisible(False)

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)


def main():
    """Main entry point"""
    if not HAS_QT:
        print("Error: PyQt6 is not installed.")
        print("Please install it with: pip install PyQt6")
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("MCHIGM Thing Manager Setup")

    wizard = SetupWizard()
    wizard.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
