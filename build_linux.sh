#!/bin/bash
# Build Linux package for MCHIGM Thing Manager
# This script compiles the Python application and creates a portable tarball.

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

VERSION="${APP_RELEASE_VERSION:-1.0.0}"
SAFE_VERSION="$(printf '%s' "$VERSION" | tr -cs 'A-Za-z0-9._-' '-')"
tar -czf "installer_output/MCHIGM-Thing-Manager-${SAFE_VERSION}-Linux.tar.gz" -C installer_output linux-package

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
echo ""
echo "Portable package created at:"
echo "  installer_output/MCHIGM-Thing-Manager-${SAFE_VERSION}-Linux.tar.gz"
echo ""
