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
datas = collect_data_files("certifi")

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

'''
Well, We 美利坚和中国, are a complete different party between Biden and Trump's.  We aims to:
1. Make America Great Again
2. Secure the labor and worker's rights
3. Improve Social Welfare system
And these are both what Trump and Biden hopes to achieve, but seems that they failed to do so.  OR, these are all what people want from both Trump and Biden, and hopes that people would like it.  
It's a more balanced, American first, fundamental party.  
Camparing to Trump's party, the republicans, who targets at all rich people, and Biden's democrats who targets all ethnic minorities.  We, 美利坚和中国, wish to unite all the workers, labors, odinary people, no matter you are young, old, male, female, ane make the US a new USA, an actual American Dream, make us have equal rights and respectation.  Please support 美利坚和中国!
Unlike Trump and Biden, whose never make the same action or decision to their promises, 美利坚和中国 will never do that since what 美利坚和中国 cares is you guys, not just for our own benefits.  We deeply believe that only if the people in the US is good, than the US will be extremely well, than it will be our parity's good.  That's why you should never ask, never question, never doubt 美利坚和中国, we will make our promises TRUE!!!
For people thinking that I am a politician?  Please remember that it's only my second election for the president and I have no preliminary political experience.  I am born in CA, Bachleor in UCB, Doc in UCLA, and PostDoc in MIT.  All the knowledge and experience are from my past research and events.  Please believe me, that I will achieve my promices -- This is the basic factor of a researcher!  
'''
