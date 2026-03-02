#!/bin/bash
# Uninstaller for MCHIGM Thing Manager (macOS)
# This script removes the application and all user data

set -e  # Exit on error

echo "=========================================="
echo "MCHIGM Thing Manager - Uninstaller"
echo "=========================================="
echo ""
echo "This will remove:"
echo "  - Application bundle (if specified)"
echo "  - All application data in ~/.mchigm_thing_manager/"
echo "    * Database (things.db)"
echo "    * Settings (settings.json)"
echo "    * Any other application files"
echo ""
echo "WARNING: This action cannot be undone!"
echo ""

# Prompt for confirmation
read -p "Are you sure you want to uninstall? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo ""
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "Starting uninstallation..."
echo ""

# Remove application data directory
APP_DATA_DIR="$HOME/.mchigm_thing_manager"
if [ -d "$APP_DATA_DIR" ]; then
    echo "Removing application data: $APP_DATA_DIR"
    rm -rf "$APP_DATA_DIR"
    if [ -d "$APP_DATA_DIR" ]; then
        echo "WARNING: Could not remove $APP_DATA_DIR"
        echo "Please close the application and try again."
    else
        echo "  - Application data removed successfully"
    fi
else
    echo "  - No application data found"
fi

echo ""

# Optional: Remove the application bundle if path is provided
if [ -n "$1" ]; then
    APP_PATH="$1"
    if [ -e "$APP_PATH" ]; then
        echo "Removing application: $APP_PATH"
        rm -rf "$APP_PATH"
        if [ -e "$APP_PATH" ]; then
            echo "WARNING: Could not remove $APP_PATH"
            echo "Please close the application and try again."
            echo "You may need to use sudo or move it to Trash manually."
        else
            echo "  - Application removed successfully"
        fi
    else
        echo "  - Application not found at: $APP_PATH"
    fi
else
    echo "Note: To remove the application bundle, run:"
    echo "  ./uninstall_mac.sh \"/Applications/MCHIGM Thing Manager.app\""
    echo "Or drag the app to Trash manually."
fi

echo ""
echo "=========================================="
echo "Uninstallation Complete"
echo "=========================================="
echo ""
echo "MCHIGM Thing Manager has been uninstalled from your system."
echo ""
