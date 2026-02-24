"""Configuration management."""
import json
import os
import sys

CONFIG_FILENAME = "claude-usage-dashboard.json"

def get_config_path():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~/.config")
    return os.path.join(base, CONFIG_FILENAME)

DEFAULT_CONFIG = {
    "port": 18080,
    "refresh_interval": 60,  # seconds
}

def load_config():
    path = get_config_path()
    if os.path.exists(path):
        with open(path) as f:
            cfg = json.load(f)
        # Merge with defaults
        return {**DEFAULT_CONFIG, **cfg}
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
