"""Load and save events to a JSON file (R5)."""

import json
import os
from pathlib import Path

DEFAULT_PATH = Path.home() / ".countdown.json"


class StorageError(Exception):
    """Raised when the events file exists but cannot be read."""


def data_path():
    """Return the events file path, honouring the COUNTDOWN_FILE override."""
    override = os.environ.get("COUNTDOWN_FILE")
    return Path(override) if override else DEFAULT_PATH


def empty_data():
    return {"next_id": 1, "events": []}


def load(path=None):
    """Load events. A missing file means no events yet."""
    path = Path(path) if path else data_path()
    if not path.exists():
        return empty_data()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise StorageError(f"Could not read events file {path}: {e}") from e
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("events"), list)
        or not isinstance(data.get("next_id"), int)
    ):
        raise StorageError(f"Events file {path} is not in the expected format.")
    return data


def save(data, path=None):
    """Write events atomically: write a temp file, then rename it over the old one."""
    path = Path(path) if path else data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
