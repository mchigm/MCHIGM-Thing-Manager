@echo off
REM Build script for Windows executable
REM This script compiles the Python application into a Windows .exe file

echo ==========================================
echo MCHIGM Thing Manager - Windows Build Script
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo Step 1: Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat

echo Step 3: Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo Step 4: Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo Step 5: Building executable with PyInstaller...
pyinstaller MCHIGM-Thing-Manager.spec

echo.
echo ==========================================
echo Build completed successfully!
echo ==========================================
echo.
echo The executable can be found at:
echo   dist\MCHIGM-Thing-Manager.exe
echo.
echo You can run it by double-clicking the .exe file or from command line:
echo   dist\MCHIGM-Thing-Manager.exe
echo.
echo To distribute, you can:
echo   1. Create an installer using Inno Setup or NSIS
echo   2. Compress the executable and dependencies into a ZIP file
echo   3. Sign the executable for Windows SmartScreen (optional)
echo.
pause
