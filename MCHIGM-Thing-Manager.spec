# -*- mode: python ; coding: utf-8 -*-
"""

MCHIGM-Thing-Manager.spec

Author: MCHIGM

Pyinstaller spec file for MCHIGM Thing Manager, builds executables for Windows and macOS.

Last Modified: 2025-05-03 (YYYY-MM-DD)

"""

import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all submodules for packages that use dynamic imports
hiddenimports = [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "sqlalchemy.sql.default_comparator",
    "sqlalchemy.ext.baked",
    "litellm",
]

# Collect data files if any
datas = []

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "pytest",
        "tk",
        "tcl",
        "_tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MCHIGM-Thing-Manager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if you have one (e.g., 'icon.ico' for Windows, 'icon.icns' for macOS)
)

# macOS app bundle configuration
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="MCHIGM Thing Manager.app",
        icon=None,  # Add icon file path here if you have one (e.g., 'icon.icns')
        bundle_identifier="com.mchigm.thing-manager",
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
        },
    )
