#!/bin/bash
# Build Linux packages for MCHIGM Thing Manager.
# Produces a portable tarball and an AppImage for wider distro compatibility.

set -e

echo "=========================================="
echo "MCHIGM Thing Manager - Linux Build Script"
echo "=========================================="
echo ""

if [[ "$OSTYPE" != "linux-gnu"* && "$OSTYPE" != "linux"* ]]; then
    echo "Error: This script must be run on Linux"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Step 1: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "Step 2: Activating virtual environment..."
source venv/bin/activate

echo "Step 3: Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "Step 4: Cleaning previous builds..."
rm -rf build dist installer_output

echo "Step 5: Building executable with PyInstaller..."
pyinstaller MCHIGM-Thing-Manager.spec

VERSION="${APP_RELEASE_VERSION:-1.0.0}"
SAFE_VERSION="$(printf '%s' "$VERSION" | tr -cs 'A-Za-z0-9._-' '-')"

echo "Step 6: Preparing portable package..."
mkdir -p installer_output/linux-package
cp dist/MCHIGM-Thing-Manager installer_output/linux-package/
if [ -f README.md ]; then
    cp README.md installer_output/linux-package/
fi
if [ -f LICENSE ]; then
    cp LICENSE installer_output/linux-package/
fi

cat > installer_output/linux-package/run.sh << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${DIR}/MCHIGM-Thing-Manager" "$@"
EOF
chmod +x installer_output/linux-package/run.sh

tar -czf "installer_output/MCHIGM-Thing-Manager-${SAFE_VERSION}-Linux.tar.gz" -C installer_output linux-package

echo "Step 7: Preparing AppImage structure..."
APPDIR="installer_output/AppDir"
APPIMAGE_TOOL="installer_output/appimagetool.AppImage"
APPIMAGE_OUTPUT="installer_output/MCHIGM-Thing-Manager-${SAFE_VERSION}-x86_64.AppImage"
DESKTOP_NAME="mchigm-thing-manager"
ICON_SOURCE="icon.png"

rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

if [ ! -f "${ICON_SOURCE}" ]; then
    echo "Error: AppImage icon not found at ${ICON_SOURCE}"
    exit 1
fi

cp dist/MCHIGM-Thing-Manager "${APPDIR}/usr/bin/"

cp "${ICON_SOURCE}" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${DESKTOP_NAME}.png"
cp "${ICON_SOURCE}" "${APPDIR}/${DESKTOP_NAME}.png"
cp "${ICON_SOURCE}" "${APPDIR}/.DirIcon"

cat > "${APPDIR}/${DESKTOP_NAME}.desktop" << EOF
[Desktop Entry]
Type=Application
Name=MCHIGM Thing Manager
Icon=${DESKTOP_NAME}
Exec=MCHIGM-Thing-Manager %U
Terminal=false
Categories=Office;
StartupNotify=true
EOF

cat > "${APPDIR}/AppRun" << 'EOF'
#!/bin/bash
APPDIR="$(cd "$(dirname "$0")" && pwd)"
exec "${APPDIR}/usr/bin/MCHIGM-Thing-Manager" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

echo "Step 8: Downloading appimagetool..."
curl -L \
    -f \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
    -o "${APPIMAGE_TOOL}"
chmod +x "${APPIMAGE_TOOL}"

echo "Step 9: Building AppImage..."
"${APPIMAGE_TOOL}" --appimage-extract-and-run "${APPDIR}"

GENERATED_APPIMAGE="$(find . -maxdepth 1 -type f -name '*.AppImage' ! -name 'appimagetool*.AppImage' -print -quit)"
if [ -z "${GENERATED_APPIMAGE}" ]; then
    echo "Error: AppImage build did not produce an output file"
    exit 1
fi
mv "${GENERATED_APPIMAGE}" "${APPIMAGE_OUTPUT}"

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
echo ""
echo "Portable package created at:"
echo "  installer_output/MCHIGM-Thing-Manager-${SAFE_VERSION}-Linux.tar.gz"
echo "AppImage created at:"
echo "  ${APPIMAGE_OUTPUT}"
echo ""
echo "You can now:"
echo "  1. Distribute the AppImage for the broadest Linux compatibility"
echo "  2. Use the tar.gz archive as a fallback for manual installs"
echo ""
echo "Notes:"
echo "  - AppImage is the recommended Linux download for most users"
echo "  - The AppImage may still require glibc and basic desktop libraries"
echo ""
