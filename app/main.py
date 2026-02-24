"""Claude Usage Dashboard - main entry point."""
import os
import sys
import threading
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config as cfg
from .chrome import scan_all_profiles
from .claude_api import fetch_all_usage

# Determine template dir (works both in dev and PyInstaller bundle)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

TEMPLATE_DIR = BASE_DIR / "templates"

app = FastAPI(title="Claude Usage Dashboard")

# State
_cached_profiles = None
_app_config = cfg.load_config()


class ConfigUpdate(BaseModel):
    refresh_interval: int | None = None
    port: int | None = None


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(TEMPLATE_DIR / "index.html") as f:
        return f.read()


@app.get("/api/usage")
async def get_usage():
    global _cached_profiles
    profiles = scan_all_profiles()
    _cached_profiles = profiles
    results = fetch_all_usage(profiles)
    # Deduplicate by email (keep first successful one)
    seen_emails = set()
    deduped = []
    for r in results:
        email = r.get("email", "unknown")
        if email == "unknown" or "error" in r:
            continue  # Skip errored profiles
        if email in seen_emails:
            continue
        seen_emails.add(email)
        deduped.append(r)
    return deduped


@app.get("/api/config")
async def get_config():
    return _app_config


@app.put("/api/config")
async def update_config(update: ConfigUpdate):
    if update.refresh_interval is not None:
        _app_config["refresh_interval"] = max(5, min(3600, update.refresh_interval))
    if update.port is not None:
        _app_config["port"] = update.port
    cfg.save_config(_app_config)
    return _app_config


def run_tray():
    """Run system tray icon."""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        print("pystray/Pillow not available, running without tray icon")
        return

    port = _app_config["port"]
    url = f"http://localhost:{port}"

    # Create a simple icon
    icon_path = BASE_DIR / "assets" / "icon.png"
    if icon_path.exists():
        image = Image.open(str(icon_path))
    else:
        # Generate a simple colored square
        image = Image.new("RGB", (64, 64), "#6366f1")

    def open_browser(icon, item):
        webbrowser.open(url)

    def quit_app(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem(f"Open Dashboard ({url})", open_browser, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )

    icon = pystray.Icon("claude-usage", image, "Claude Usage Dashboard", menu)
    icon.run()


def main():
    port = _app_config["port"]

    # Open browser after short delay
    def open_delayed():
        import time
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=open_delayed, daemon=True).start()

    if sys.platform == "darwin":
        # macOS: pystray needs main thread, run server in background
        threading.Thread(
            target=lambda: uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning"),
            daemon=True,
        ).start()
        run_tray()  # blocks on main thread
    else:
        # Windows/Linux: tray in background, server on main thread
        threading.Thread(target=run_tray, daemon=True).start()
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
