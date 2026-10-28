"""Persistence module for player settings using JSON."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from config import (
    DEFAULT_DIFFICULTY,
    SETTINGS_FILE,
)

logger = logging.getLogger(__name__)


def ensure_data_directory(file_path: Path) -> None:
    """Ensure parent directory exists."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logger.warning("Failed to create data directory for %s: %s", file_path, exc)


def load_settings(file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load settings from JSON with default fallbacks."""
    default_settings: Dict[str, Any] = {
        "difficulty": DEFAULT_DIFFICULTY,
    }

    path = file_path or SETTINGS_FILE
    if not path.exists():
        return default_settings

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                default_settings.update(data)
                return default_settings
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Error reading settings from '%s': %s. Using defaults.", path, exc)

    return default_settings


def save_settings(settings: Dict[str, Any], file_path: Optional[Path] = None) -> bool:
    """Save user settings to JSON."""
    path = file_path or SETTINGS_FILE
    ensure_data_directory(path)

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True
    except OSError as exc:
        logger.error("Failed to write settings to '%s': %s", path, exc)
        return False
