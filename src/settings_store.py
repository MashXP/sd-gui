import json
import os

SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "settings.json"
)

def read_settings():
    """Reads persisted UI settings, returning an empty dict on any problem."""
    try:
        if not os.path.exists(SETTINGS_PATH):
            return {}
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def write_setting(key, value):
    """Persists a single setting key, leaving all other keys untouched."""
    settings = read_settings()
    settings[key] = value
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, sort_keys=True)
            f.write("\n")
    except Exception:
        pass
