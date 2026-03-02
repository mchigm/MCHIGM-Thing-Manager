#!/bin/bash
# Build macOS .pkg installer for MCHIGM Thing Manager
# This script creates a macOS installer package

set -e  # Exit on error

echo "=========================================="
echo "Building macOS .pkg Installer"
echo "=========================================="
echo ""

# Configuration
APP_NAME="MCHIGM Thing Manager"
APP_BUNDLE="MCHIGM Thing Manager.app"
VERSION="1.0.0"
BUNDLE_ID="com.mchigm.thing-manager"
PKG_NAME="MCHIGM-Thing-Manager-${VERSION}.pkg"

# Directories
BUILD_DIR="$(pwd)/pkg_build"
SCRIPTS_DIR="${BUILD_DIR}/scripts"
PAYLOAD_DIR="${BUILD_DIR}/payload"
RESOURCES_DIR="${BUILD_DIR}/resources"

echo "Step 1: Checking prerequisites..."

# Check if the app bundle exists
if [ ! -d "dist/${APP_BUNDLE}" ]; then
    echo "Error: Application bundle not found at dist/${APP_BUNDLE}"
    echo "Please build the application first using: ./build_mac.sh"
    exit 1
fi

# Check if pkgbuild is available
if ! command -v pkgbuild &> /dev/null; then
    echo "Error: pkgbuild command not found"
    echo "This script requires macOS with Xcode Command Line Tools"
    exit 1
fi

echo "Step 2: Creating build directories..."
rm -rf "${BUILD_DIR}"
mkdir -p "${SCRIPTS_DIR}"
mkdir -p "${PAYLOAD_DIR}/Applications"
mkdir -p "${RESOURCES_DIR}"

echo "Step 3: Copying application bundle..."
cp -R "dist/${APP_BUNDLE}" "${PAYLOAD_DIR}/Applications/"

echo "Step 4: Creating installation scripts..."

# Create postinstall script
cat > "${SCRIPTS_DIR}/postinstall" << 'EOF'
#!/bin/bash
# Post-installation script for MCHIGM Thing Manager

# Get the user who invoked sudo (if any)
if [ -n "$SUDO_USER" ]; then
    ACTUAL_USER="$SUDO_USER"
else
    ACTUAL_USER="$USER"
fi

# Validate username to contain only safe characters
if ! printf '%s\n' "$ACTUAL_USER" | grep -Eq '^[A-Za-z0-9_][A-Za-z0-9_.-]*$'; then
    echo "Error: Unsafe username detected: $ACTUAL_USER" >&2
    exit 1
fi

# Get the user's home directory in a safe way
USER_HOME=$(/usr/bin/dscl . -read "/Users/${ACTUAL_USER}" NFSHomeDirectory 2>/dev/null | awk '{print $2}')

# Fallback to HOME if dscl fails and ACTUAL_USER is the current user
if [ -z "$USER_HOME" ]; then
    if [ "$ACTUAL_USER" = "$USER" ] && [ -n "$HOME" ]; then
        USER_HOME="$HOME"
    else
        echo "Error: Could not determine home directory for user ${ACTUAL_USER}" >&2
        exit 1
    fi
fi
# Create data directory
DATA_DIR="${USER_HOME}/.mchigm_thing_manager"
mkdir -p "${DATA_DIR}"

# Set ownership to the actual user
chown -R "$ACTUAL_USER" "${DATA_DIR}"

echo "MCHIGM Thing Manager has been installed successfully!"
echo "Data directory created at: ${DATA_DIR}"

exit 0
EOF

chmod +x "${SCRIPTS_DIR}/postinstall"

# Create preinstall script
cat > "${SCRIPTS_DIR}/preinstall" << 'EOF'
#!/bin/bash
# Pre-installation script for MCHIGM Thing Manager

echo "Preparing to install MCHIGM Thing Manager..."

# Check if app is running
APP_PROCESS="MCHIGM-Thing-Manager"
if pgrep -x "$APP_PROCESS" > /dev/null; then
    echo "Warning: MCHIGM Thing Manager is currently running."
    echo "Please close the application before installing."

    # Optionally, we could force quit here
    # osascript -e 'quit app "MCHIGM Thing Manager"'
fi

exit 0
EOF

chmod +x "${SCRIPTS_DIR}/preinstall"

echo "Step 5: Creating Welcome and ReadMe files..."

# Create Welcome.txt
cat > "${RESOURCES_DIR}/Welcome.txt" << EOF
Welcome to MCHIGM Thing Manager ${VERSION}

This installer will install MCHIGM Thing Manager on your Mac.

MCHIGM Thing Manager is an AI-powered desktop time management application
with task tracking, calendar integration, and intelligent planning features.

Features:
• Kanban-style task board (TODOs)
• Calendar integration (Timetable)
• AI-powered memo and planning
• Gantt chart roadmaps
• Cross-scenario tagging

The application will be installed in your Applications folder.
Application data will be stored in ~/.mchigm_thing_manager/

Click Continue to proceed with the installation.
EOF

# Create ReadMe.txt
cat > "${RESOURCES_DIR}/ReadMe.txt" << EOF
MCHIGM Thing Manager ${VERSION}
===============================

Thank you for installing MCHIGM Thing Manager!

GETTING STARTED
---------------
1. Launch "MCHIGM Thing Manager" from your Applications folder
2. The app will create its database on first launch
3. Configure AI settings in Settings > AI Agent (optional)

DATA LOCATION
-------------
Application data is stored at:
  ~/.mchigm_thing_manager/

This includes:
  - things.db (SQLite database)
  - settings.json (application settings)

REQUIREMENTS
------------
• macOS 10.13 (High Sierra) or later
• No additional software required

SUPPORT
-------
For issues and feature requests:
  https://github.com/mchigm/MCHIGM-Thing-Manager/issues

Documentation:
  https://github.com/mchigm/MCHIGM-Thing-Manager

LICENSE
-------
See LICENSE file for license information.

UNINSTALLATION
--------------
To uninstall:
1. Drag "MCHIGM Thing Manager.app" from Applications to Trash
2. Remove data directory: rm -rf ~/.mchigm_thing_manager

Or use the uninstall script:
  ./uninstall_mac.sh "/Applications/MCHIGM Thing Manager.app"
EOF

echo "Step 6: Building component package..."
pkgbuild --root "${PAYLOAD_DIR}" \
         --scripts "${SCRIPTS_DIR}" \
         --identifier "${BUNDLE_ID}" \
         --version "${VERSION}" \
         --install-location "/" \
         "${BUILD_DIR}/component.pkg"

echo "Step 7: Creating distribution XML..."
cat > "${BUILD_DIR}/distribution.xml" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>${APP_NAME}</title>
    <organization>${BUNDLE_ID}</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false" hostArchitectures="x86_64,arm64"/>

    <welcome file="Welcome.txt" mime-type="text/plain" />
    <readme file="ReadMe.txt" mime-type="text/plain" />
    <license file="license.txt" mime-type="text/plain" />

    <pkg-ref id="${BUNDLE_ID}"/>

    <choices-outline>
        <line choice="default">
            <line choice="${BUNDLE_ID}"/>
        </line>
    </choices-outline>

    <choice id="default"/>
    <choice id="${BUNDLE_ID}" visible="false">
        <pkg-ref id="${BUNDLE_ID}"/>
    </choice>

    <pkg-ref id="${BUNDLE_ID}" version="${VERSION}" onConclusion="none">
        component.pkg
    </pkg-ref>
</installer-gui-script>
EOF

# Copy license file
if [ -f "LICENSE" ]; then
    cp LICENSE "${RESOURCES_DIR}/license.txt"
else
    echo "No LICENSE file found" > "${RESOURCES_DIR}/license.txt"
fi

# Create installer_output directory if it doesn't exist
mkdir -p installer_output

echo "Step 8: Building product archive..."
productbuild --distribution "${BUILD_DIR}/distribution.xml" \
             --resources "${RESOURCES_DIR}" \
             --package-path "${BUILD_DIR}" \
             "installer_output/${PKG_NAME}"
echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
echo ""
echo "Installer created at:"
echo "  installer_output/${PKG_NAME}"
echo ""
echo "You can now:"
echo "  1. Test the installer: open installer_output/${PKG_NAME}"
echo "  2. Distribute the .pkg file to users"
echo ""
echo "Notes:"
echo "  - For distribution outside the App Store, consider code signing"
echo "  - For notarization, you'll need an Apple Developer account"
echo ""
