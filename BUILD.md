# Building Executables for MCHIGM Thing Manager

This guide explains how to compile the MCHIGM Thing Manager Python application into standalone executables for Windows and macOS.

## Overview

The application uses PyInstaller to create standalone executables that bundle Python and all dependencies into a single distributable package.

## Prerequisites

### For Windows
- Python 3.8 or higher
- Windows 10 or higher
- Git (optional, for cloning the repository)

### For macOS
- Python 3.8 or higher
- macOS 10.13 (High Sierra) or higher
- Xcode Command Line Tools (install with `xcode-select --install`)

## Quick Start

### Building Executables

#### Windows

1. Open Command Prompt or PowerShell
2. Navigate to the project directory
3. Run the build script:
   ```batch
   build_windows.bat
   ```
4. The executable will be created at `dist\MCHIGM-Thing-Manager.exe`

#### macOS

1. Open Terminal
2. Navigate to the project directory
3. Run the build script:
   ```bash
   ./build_mac.sh
   ```
4. The application bundle will be created at `dist/MCHIGM Thing Manager.app`

### Building Installers

For easier distribution, you can create professional installers:

#### Windows Installer (.exe)

1. Build the executable first (see above)
2. Install [Inno Setup 6](https://jrsoftware.org/isdl.php)
3. Run the installer build script:
   ```batch
   build_windows_installer.bat
   ```
4. The installer will be created at `installer_output\MCHIGM-Thing-Manager-Setup.exe`

#### macOS Installer (.pkg)

1. Build the application bundle first (see above)
2. Run the pkg build script:
   ```bash
   ./build_macos_pkg.sh
   ```
3. The installer will be created at `installer_output/MCHIGM-Thing-Manager-1.0.0.pkg`

## Manual Build Process

If you prefer to build manually or need to customize the build process:

### Step 1: Set up virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies (includes PyInstaller)
pip install -r requirements-dev.txt
```

### Step 3: Build the executable

```bash
# Build using the spec file
pyinstaller MCHIGM-Thing-Manager.spec
```

### Step 4: Find your executable

- **Windows**: `dist\MCHIGM-Thing-Manager.exe`
- **macOS**: `dist/MCHIGM Thing Manager.app`

## Customizing the Build

### Spec File Configuration

The `MCHIGM-Thing-Manager.spec` file controls the build process. You can customize:

- **Application Icon**: Set the `icon` parameter in the spec file
  - Windows: Use `.ico` format
  - macOS: Use `.icns` format

- **Hidden Imports**: Add any missing modules to the `hiddenimports` list

- **Excluded Modules**: Add modules you don't need to the `excludes` list to reduce size

- **Console Window**: Change `console=False` to `console=True` if you want a console window (useful for debugging)

### Adding an Application Icon

1. Create or obtain icon files:
   - Windows: `icon.ico` (256x256 recommended)
   - macOS: `icon.icns` (multiple sizes, 1024x1024 down to 16x16)

2. Place the icon file in the project root directory

3. Edit `MCHIGM-Thing-Manager.spec`:
   ```python
   # For the EXE section
   icon='icon.ico',  # Windows

   # For the BUNDLE section (macOS)
   icon='icon.icns',
   ```

4. Rebuild the application

## Distribution

### Setup Wizard

A comprehensive setup wizard is provided for managing the application installation:

```bash
# Run the setup wizard
python setup_wizard.py
```

The setup wizard provides:
- **Install**: Install the application with configurable options
- **Test**: Verify installation integrity
- **Repair**: Fix corrupted installations and backup data
- **Settings**: View and modify application settings
- **Uninstall**: Remove the application and optionally user data

The wizard requires PyQt6 and provides a user-friendly GUI for all installation operations.

### Windows Distribution

1. **Simple ZIP Distribution**:
   - Compress `dist\MCHIGM-Thing-Manager.exe` into a ZIP file
   - Users extract and run the .exe file

2. **Professional Installer** (Recommended):
   - Use the provided Inno Setup script: `installer_windows.iss`
   - Run `build_windows_installer.bat` to create the installer
   - Creates a professional installer with:
     - Start Menu and Desktop shortcuts
     - Custom installation directory selection
     - Automatic data directory creation
     - Proper uninstallation with data cleanup options
     - Windows-standard installation wizard

   **Features of the Windows Installer:**
   - Automatic detection of previous installations
   - Option to create desktop and quick launch icons
   - Configurable data directory location
   - Clean uninstallation with optional data removal
   - Professional installation wizard UI

3. **Code Signing** (Optional but Recommended):
   - Sign the executable to avoid Windows SmartScreen warnings
   - Requires a code signing certificate
   - Improves user trust and reduces security warnings

### macOS Distribution

1. **Simple ZIP Distribution**:
   - Right-click `dist/MCHIGM Thing Manager.app`
   - Choose "Compress"
   - Share the resulting ZIP file

2. **Professional .pkg Installer** (Recommended):
   - Use the provided build script: `build_macos_pkg.sh`
   - Creates a native macOS installer package with:
     - Welcome and ReadMe screens
     - License agreement display
     - Automatic installation to /Applications
     - Data directory creation in user home
     - Pre/post-installation scripts
     - Native macOS installer UI

   **Features of the macOS Installer:**
   - Standard macOS installer experience
   - Automatic data directory setup
   - Configurable installation options
   - Proper permissions handling
   - Support for both Intel and Apple Silicon

3. **DMG Distribution** (Alternative):
   - Use tools like `create-dmg` or `appdmg`
   - Creates a professional disk image with drag-to-Applications
   - More visual but less automated than .pkg

4. **Notarization** (For public distribution):
   - Required for macOS 10.15 (Catalina) and later
   - Requires an Apple Developer account ($99/year)
   - Prevents Gatekeeper warnings
   - Command: `xcrun notarytool submit`

### Installer Comparison

| Feature | Windows (Inno Setup) | macOS (.pkg) |
|---------|---------------------|--------------|
| Native UI | ✓ | ✓ |
| Custom install location | ✓ | ✓ |
| Desktop shortcuts | ✓ | N/A |
| Data directory setup | ✓ | ✓ |
| Uninstall with data cleanup | ✓ | Manual |
| Code signing support | ✓ | ✓ |
| Automatic updates | Via script | Via script |

## Troubleshooting

### Build Issues

**Problem**: Missing modules error during runtime
- **Solution**: Add the missing module to `hiddenimports` in the spec file

**Problem**: Large executable size
- **Solution**: Add unnecessary packages to `excludes` in the spec file

**Problem**: Application crashes on startup
- **Solution**: Run with `console=True` in the spec file to see error messages

### Platform-Specific Issues

**Windows**: Antivirus flags the executable
- **Solution**: This is common with PyInstaller. Code signing helps, or create an exception

**macOS**: "App is damaged and can't be opened"
- **Solution**: This happens if the app isn't signed. Users can bypass with:
  ```bash
  xattr -cr "/path/to/MCHIGM Thing Manager.app"
  ```

**macOS**: Application won't open (Gatekeeper)
- **Solution**: Right-click → Open (first time only) or sign/notarize the app

## Advanced Topics

### Cross-Compilation

PyInstaller **does not support cross-compilation**. You must build on each target platform:
- Windows executables must be built on Windows
- macOS applications must be built on macOS

You can use:
- Virtual machines (VirtualBox, VMware)
- CI/CD services (GitHub Actions, CircleCI) that support multiple platforms
- Cloud build services

### Continuous Integration

Example GitHub Actions workflow for automated builds:

```yaml
name: Build Executables

on: [push, pull_request]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: build_windows.bat
      - uses: actions/upload-artifact@v3
        with:
          name: windows-executable
          path: dist/MCHIGM-Thing-Manager.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: ./build_mac.sh
      - uses: actions/upload-artifact@v3
        with:
          name: macos-app
          path: dist/MCHIGM Thing Manager.app
```

### Reducing Executable Size

1. Use UPX compression (enabled by default in spec file)
2. Exclude unnecessary packages in the spec file
3. Use `--onefile` mode carefully (it's slower to start)
4. Remove debug symbols with `strip=True`

### Testing the Build

Before distributing:

1. Test on a clean machine without Python installed
2. Test all major features of the application
3. Check that database creation works in user directories
4. Verify all UI elements render correctly
5. Test file permissions and paths

## Uninstallation

To completely remove MCHIGM Thing Manager from your system, use the provided uninstaller scripts.

### Uninstalling on Windows

1. Run the uninstaller script:
   ```batch
   uninstall_windows.bat
   ```

2. To also remove the executable, provide its path:
   ```batch
   uninstall_windows.bat "C:\path\to\MCHIGM-Thing-Manager.exe"
   ```

3. Follow the prompts to confirm uninstallation

### Uninstalling on macOS

1. Run the uninstaller script:
   ```bash
   ./uninstall_mac.sh
   ```

2. To also remove the application bundle, provide its path:
   ```bash
   ./uninstall_mac.sh "/Applications/MCHIGM Thing Manager.app"
   ```

3. Alternatively, you can manually:
   - Drag the app from Applications to Trash
   - Run: `rm -rf ~/.mchigm_thing_manager`

### What Gets Removed

The uninstaller removes:
- **Application Data**: `~/.mchigm_thing_manager/` (Windows: `%USERPROFILE%\.mchigm_thing_manager\`)
  - Database file: `things.db`
  - Settings file: `settings.json`
- **Executable/App Bundle**: If path is provided to the uninstaller

**Important**: Uninstallation is permanent and cannot be undone. Make sure to back up your data if needed before uninstalling.

## Support

For build issues, check:
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [PyInstaller GitHub Issues](https://github.com/pyinstaller/pyinstaller/issues)

## File Structure

After building, your project will have:

```
MCHIGM-Thing-Manager/
├── build/              # Temporary build files (can be deleted)
├── dist/               # Final executables (distribute this)
│   ├── MCHIGM-Thing-Manager.exe          # Windows
│   └── MCHIGM Thing Manager.app/         # macOS
├── installer_output/   # Generated installers
│   ├── MCHIGM-Thing-Manager-Setup.exe    # Windows installer
│   └── MCHIGM-Thing-Manager-1.0.0.pkg    # macOS installer
├── pkg_build/          # Temporary pkg build files (can be deleted)
├── venv/               # Virtual environment (don't distribute)
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── MCHIGM-Thing-Manager.spec      # PyInstaller configuration
├── build_windows.bat              # Windows executable builder
├── build_mac.sh                   # macOS executable builder
├── build_windows_installer.bat    # Windows installer builder
├── build_macos_pkg.sh             # macOS pkg installer builder
├── installer_windows.iss          # Inno Setup script
├── setup_wizard.py                # Setup wizard (install/repair/test/uninstall)
├── uninstall_windows.bat          # Windows uninstaller
├── uninstall_mac.sh               # macOS uninstaller
└── BUILD.md                       # This file
```

## License

Ensure your distribution complies with the licenses of all dependencies, especially:
- PyQt6 (GPL or commercial license)
- SQLAlchemy (MIT)
- litellm (MIT)
