@echo off
title Manu AI Assistant — Siri Mode
cd /d "%~dp0"
echo Starting Manu in Siri Mode...
echo No window will open. Check your system tray (bottom-right).
echo Say "Hey Manu" to talk. Right-click tray icon to quit.
echo.
pythonw main.py --siri
if errorlevel 1 (
    echo.
    echo Manu failed to start. Running diagnostic...
    python main.py --siri
    pause
)
