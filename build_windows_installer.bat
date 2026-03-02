@echo off
REM Build Windows installer using Inno Setup
REM This script compiles the Inno Setup script to create a Windows installer

echo ==========================================
echo Building Windows Installer
echo ==========================================
echo.

REM Check if Inno Setup is installed
set "INNO_SETUP=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist "%INNO_SETUP%" (
    echo Error: Inno Setup not found at: %INNO_SETUP%
    echo.
    echo Please install Inno Setup 6 from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo After installation, you may need to update the INNO_SETUP variable
    echo in this script to point to the correct location.
    pause
    exit /b 1
)

REM Check if the executable exists
if not exist "dist\MCHIGM-Thing-Manager.exe" (
    echo Error: Executable not found at dist\MCHIGM-Thing-Manager.exe
    echo.
    echo Please build the application first using:
    echo   build_windows.bat
    pause
    exit /b 1
)

REM Create installer_output directory
if not exist "installer_output" mkdir installer_output

echo Step 1: Compiling Inno Setup script...
"%INNO_SETUP%" "installer_windows.iss"

if errorlevel 1 (
    echo.
    echo Error: Inno Setup compilation failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build completed successfully!
echo ==========================================
echo.
echo Installer created at:
echo   installer_output\MCHIGM-Thing-Manager-Setup.exe
echo.
echo You can now:
echo   1. Test the installer: installer_output\MCHIGM-Thing-Manager-Setup.exe
echo   2. Distribute the installer to users
echo.
echo Notes:
echo   - Consider code signing for production distribution
echo   - Test on a clean Windows installation
echo.
pause
