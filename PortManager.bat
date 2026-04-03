@echo off
title PortManager TUI
:: Change directory to the location of this script
cd /d "%~dp0"

:: Check if a virtual environment exists and use it, otherwise use global python
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)
