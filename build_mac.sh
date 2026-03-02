#!/bin/bash
# Build script for macOS executable
# This script compiles the Python application into a macOS .app bundle

set -e  # Exit on error

echo "=========================================="
echo "MCHIGM Thing Manager - macOS Build Script"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script must be run on macOS"
    exit 1
fi

# Check if Python is available
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
rm -rf build dist

echo "Step 5: Building executable with PyInstaller..."
pyinstaller MCHIGM-Thing-Manager.spec

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
echo ""
echo "The application bundle can be found at:"
echo "  dist/MCHIGM Thing Manager.app"
echo ""
echo "You can run it by double-clicking or using:"
echo "  open \"dist/MCHIGM Thing Manager.app\""
echo ""
echo "To distribute, you can:"
echo "  1. Create a DMG file for distribution"
echo "  2. Compress the .app bundle into a ZIP file"
echo "  3. Notarize for macOS Gatekeeper (requires Apple Developer account)"
echo ""
