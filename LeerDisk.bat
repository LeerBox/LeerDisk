@echo off
title LeerDisk
python "%~dp0main.py" %*
if errorlevel 1 (
    echo.
    echo  LeerDisk exited with an error.
    echo  If dependencies are missing, run install.bat first.
    echo.
    pause
)
