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

### Building on Windows

1. Open Command Prompt or PowerShell
2. Navigate to the project directory
3. Run the build script:
   ```batch
   build_windows.bat
   ```
4. The executable will be created at `dist\MCHIGM-Thing-Manager.exe`

### Building on macOS

1. Open Terminal
2. Navigate to the project directory
3. Run the build script:
   ```bash
   ./build_mac.sh
   ```
4. The application bundle will be created at `dist/MCHIGM Thing Manager.app`

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

### Windows Distribution

1. **Simple ZIP Distribution**:
   - Compress `dist\MCHIGM-Thing-Manager.exe` into a ZIP file
   - Users extract and run the .exe file

2. **Create an Installer** (Recommended):
   - Use [Inno Setup](https://jrsoftware.org/isinfo.php) (free)
   - Or [NSIS](https://nsis.sourceforge.io/) (free)
   - Creates a professional installer with Start Menu shortcuts

3. **Code Signing** (Optional):
   - Sign the executable to avoid Windows SmartScreen warnings
   - Requires a code signing certificate

### macOS Distribution

1. **Simple ZIP Distribution**:
   - Right-click `dist/MCHIGM Thing Manager.app`
   - Choose "Compress"
   - Share the resulting ZIP file

2. **Create a DMG** (Recommended):
   - Use tools like `create-dmg` or `appdmg`
   - Creates a professional disk image with drag-to-Applications

3. **Notarization** (For public distribution):
   - Required for macOS 10.15 (Catalina) and later
   - Requires an Apple Developer account ($99/year)
   - Prevents Gatekeeper warnings

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
├── venv/               # Virtual environment (don't distribute)
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── MCHIGM-Thing-Manager.spec
├── build_windows.bat
├── build_mac.sh
└── BUILD.md            # This file
```

## License

Ensure your distribution complies with the licenses of all dependencies, especially:
- PyQt6 (GPL or commercial license)
- SQLAlchemy (MIT)
- litellm (MIT)
