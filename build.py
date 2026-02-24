#!/usr/bin/env python3
"""Build script for PyInstaller packaging."""
import PyInstaller.__main__
import sys

PyInstaller.__main__.run([
    "app/main.py",
    "--name=Claude-Usage-Dashboard",
    "--onefile",
    "--windowed",
    "--add-data=app/templates:app/templates",
    "--add-data=assets:assets",
    "--hidden-import=app",
    "--hidden-import=app.chrome",
    "--hidden-import=app.claude_api",
    "--hidden-import=app.config",
    "--icon=assets/icon.ico" if sys.platform == "win32" else "--icon=assets/icon.png",
    "--noconfirm",
])
