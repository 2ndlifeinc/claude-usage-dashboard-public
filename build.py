#!/usr/bin/env python3
"""Build script for PyInstaller packaging."""
import os
import sys
import PyInstaller.__main__

args = [
    "app/main.py",
    "--name=Claude-Usage-Dashboard",
    "--onefile",
    "--windowed",
    "--add-data=app/templates" + os.pathsep + "app/templates",
    "--hidden-import=app",
    "--hidden-import=app.chrome",
    "--hidden-import=app.claude_api",
    "--hidden-import=app.config",
    "--noconfirm",
]

if os.path.isdir("assets"):
    args.append("--add-data=assets" + os.pathsep + "assets")

if sys.platform == "win32" and os.path.exists("assets/icon.ico"):
    args.append("--icon=assets/icon.ico")
elif os.path.exists("assets/icon.png"):
    args.append("--icon=assets/icon.png")

PyInstaller.__main__.run(args)
