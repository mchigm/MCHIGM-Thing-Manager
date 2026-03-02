#!/usr/bin/env python3
"""
Pre-build validation script for MCHIGM Thing Manager
Checks that all dependencies are installed before attempting to build executables
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python version {version.major}.{version.minor} is too old. Need Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_module(module_name, package_name=None):
    """Check if a Python module is installed"""
    if package_name is None:
        package_name = module_name

    try:
        __import__(module_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - Not installed")
        return False


def check_files():
    """Check if required build files exist"""
    required_files = [
        'main.py',
        'requirements.txt',
        'requirements-dev.txt',
        'MCHIGM-Thing-Manager.spec',
    ]

    all_exist = True
    for filename in required_files:
        path = Path(filename)
        if path.exists():
            print(f"✅ {filename}")
        else:
            print(f"❌ {filename} - Not found")
            all_exist = False

    return all_exist


def main():
    print("=" * 60)
    print("MCHIGM Thing Manager - Pre-Build Validation")
    print("=" * 60)
    print()

    print("Checking Python version...")
    python_ok = check_python_version()
    print()

    print("Checking required files...")
    files_ok = check_files()
    print()

    print("Checking runtime dependencies...")
    runtime_deps = [
        ('PyQt6', 'PyQt6'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('litellm', 'litellm'),
    ]
    runtime_ok = all(check_module(mod, pkg) for mod, pkg in runtime_deps)
    print()

    print("Checking development dependencies...")
    dev_deps = [
        ('PyInstaller', 'pyinstaller'),
    ]
    dev_ok = all(check_module(mod, pkg) for mod, pkg in dev_deps)
    print()

    print("=" * 60)
    if python_ok and files_ok and runtime_ok and dev_ok:
        print("✅ All checks passed! Ready to build.")
        print()
        print("Next steps:")
        print("  - Windows: Run build_windows.bat")
        print("  - macOS:   Run ./build_mac.sh")
        print("  - Manual:  Run pyinstaller MCHIGM-Thing-Manager.spec")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        if not runtime_ok:
            print("To install runtime dependencies:")
            print("  pip install -r requirements.txt")
            print()
        if not dev_ok:
            print("To install development dependencies:")
            print("  pip install -r requirements-dev.txt")
            print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
