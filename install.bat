@echo off
title LeerDisk - Installer
color 0B
echo.
echo  =============================================
echo    LeerDisk  ^|  Installing Dependencies
echo  =============================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python was not found in PATH.
    echo  Please install Python 3.10+ from https://python.org
    echo  and make sure to tick "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo  Python found. Installing required libraries...
echo.
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo.
if errorlevel 1 (
    echo  [ERROR] One or more packages failed to install.
    echo  Try running: pip install customtkinter psutil pillow
) else (
    echo  =============================================
    echo    All dependencies installed successfully!
    echo    Run LeerDisk.bat to start the application.
    echo  =============================================
)
echo.
pause
