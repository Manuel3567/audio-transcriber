import json
from pathlib import Path


def load_device_config() -> dict:
    """Load device IDs from config.json. Returns empty dict if missing."""
    config_path = Path.cwd() / "config.json"
    if not config_path.exists():
        return {}
    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_device_config(config: dict) -> None:
    """Save device config to config.json."""
    with open(Path.cwd() / "config.json", "w") as f:
        json.dump(config, f, indent=2)
