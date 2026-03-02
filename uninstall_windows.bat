@echo off
REM Uninstaller for MCHIGM Thing Manager (Windows)
REM This script removes the application and all user data

setlocal enabledelayedexpansion

echo ==========================================
echo MCHIGM Thing Manager - Uninstaller
echo ==========================================
echo.
echo This will remove:
echo   - Application executable (if specified)
echo   - All application data in %USERPROFILE%\.mchigm_thing_manager\
echo     * Database (things.db)
echo     * Settings (settings.json)
echo     * Any other application files
echo.
echo WARNING: This action cannot be undone!
echo.

set /p "CONFIRM=Are you sure you want to uninstall? (yes/no): "
if /i not "%CONFIRM%"=="yes" (
    echo.
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo Starting uninstallation...
echo.

REM Remove application data directory
set "APP_DATA_DIR=%USERPROFILE%\.mchigm_thing_manager"
if exist "%APP_DATA_DIR%" (
    echo Removing application data: %APP_DATA_DIR%
    rmdir /s /q "%APP_DATA_DIR%"
    if exist "%APP_DATA_DIR%" (
        echo WARNING: Could not remove %APP_DATA_DIR%
        echo Please close the application and try again.
    ) else (
        echo   - Application data removed successfully
    )
) else (
    echo   - No application data found
)

echo.

REM Optional: Remove the executable if path is provided
if not "%~1"=="" (
    set "EXE_PATH=%~1"
    if exist "!EXE_PATH!" (
        echo Removing executable: !EXE_PATH!
        del /f /q "!EXE_PATH!"
        if exist "!EXE_PATH!" (
            echo WARNING: Could not remove !EXE_PATH!
            echo Please close the application and try again.
        ) else (
            echo   - Executable removed successfully
        )
    ) else (
        echo   - Executable not found at: !EXE_PATH!
    )
) else (
    echo Note: To remove the executable, run:
    echo   uninstall_windows.bat "path\to\MCHIGM-Thing-Manager.exe"
)

echo.
echo ==========================================
echo Uninstallation Complete
echo ==========================================
echo.
echo MCHIGM Thing Manager has been uninstalled from your system.
echo.

pause
