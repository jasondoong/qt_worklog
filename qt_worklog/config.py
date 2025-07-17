import os
import json
from pathlib import Path
import sys

from PySide6.QtWidgets import QMessageBox


class ConfigError(Exception):
    pass


def get_config_dir() -> Path:
    return Path.home() / ".config" / "worklog"


def load_config(filename: str, env_prefix: str) -> dict:
    config_dir = get_config_dir()
    config_file = config_dir / filename

    if config_file.exists():
        with open(config_file, "r") as f:
            return json.load(f)
    else:
        config = {}
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                config[config_key] = value
        if config:
            return config

    raise ConfigError(f"Configuration file {filename} not found and no environment variables set.")


def handle_config_error(app, e: ConfigError):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setText(str(e))
    msg_box.setWindowTitle("Configuration Error")
    msg_box.exec()
    sys.exit(1)


FIREBASE_CONFIG = None
GOOGLE_OAUTH_CLIENT_CONFIG = None

def load_all_configs():
    global FIREBASE_CONFIG, GOOGLE_OAUTH_CLIENT_CONFIG
    FIREBASE_CONFIG = load_config("firebase_config.json", "WORKLOG_FB_")
    GOOGLE_OAUTH_CLIENT_CONFIG = load_config("google_oauth_client.json", "WORKLOG_GOOGLE_")
