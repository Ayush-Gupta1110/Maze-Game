"""Centralized configuration and constants for Maze Explorer."""

from pathlib import Path
from typing import Dict, Any, Tuple

# Window & Display
GAME_TITLE: str = "Maze Explorer"
DEFAULT_WINDOW_WIDTH: int = 1024
DEFAULT_WINDOW_HEIGHT: int = 768
TARGET_FPS: int = 60

# Directory paths
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
SETTINGS_FILE: Path = DATA_DIR / "settings.json"
ASSETS_DIR: Path = BASE_DIR / "assets"

# Color Palette (Dark Neon Theme)
COLOR_BG: Tuple[int, int, int] = (13, 17, 23)           # #0d1117 Deep midnight
COLOR_PANEL_BG: Tuple[int, int, int] = (22, 27, 34)     # #161b22 HUD / Panel dark
COLOR_PANEL_BORDER: Tuple[int, int, int] = (48, 54, 61) # #30363d Panel border
COLOR_WALL: Tuple[int, int, int] = (30, 41, 59)          # #1e293b Slate wall
COLOR_WALL_BORDER: Tuple[int, int, int] = (51, 65, 85)   # #334155 Wall outline
COLOR_PATH: Tuple[int, int, int] = (15, 23, 42)          # #0f172a Deep walkable path

# Interactive Elements
COLOR_PLAYER: Tuple[int, int, int] = (0, 240, 255)       # Cyan neon
COLOR_PLAYER_GLOW: Tuple[int, int, int] = (0, 180, 220)
COLOR_AGENT: Tuple[int, int, int] = (244, 63, 94)        # Crimson Rose neon rival agent
COLOR_AGENT_GLOW: Tuple[int, int, int] = (225, 29, 72)   # Deep Crimson Glow
COLOR_AGENT_TRAIL: Tuple[int, int, int] = (251, 113, 133) # Agent path trail
COLOR_START: Tuple[int, int, int] = (16, 185, 129)       # Emerald green
COLOR_EXIT: Tuple[int, int, int] = (245, 158, 11)        # Radiant Amber/Gold
COLOR_EXIT_LOCKED: Tuple[int, int, int] = (168, 85, 247) # Violet lock
COLOR_KEY: Tuple[int, int, int] = (251, 191, 36)         # Golden key
COLOR_COIN: Tuple[int, int, int] = (250, 204, 21)        # Yellow coin
COLOR_GEM: Tuple[int, int, int] = (192, 132, 252)        # Purple amethyst gem
COLOR_HINT_PATH: Tuple[int, int, int] = (56, 189, 248)   # Sky cyan hint dots
COLOR_PREVIEW_BAR: Tuple[int, int, int] = (56, 189, 248) # Countdown bar color

# Game Modes
MODE_RACE: str = "race"     # Compete with the Agent (Clear Preview -> Blindness -> Race)
MODE_SOLO: str = "solo"     # Solo exploration

# Fixed Maze Grid Size (Always 25x25 as requested)
MAZE_GRID_SIZE: int = 25
MAZE_ROWS: int = 25
MAZE_COLS: int = 25

# Memorization and Blindness Mode Settings
PREVIEW_DURATION: float = 4.0            # Default seconds clear maze is shown to memorize
BLIND_VISION_RADIUS_CELLS: float = 2.4   # Radius of visibility when blind is on
AGENT_STEP_SPEEDS: Dict[str, float] = {
    "Easy": 0.44,       # 0.44s per tile (relaxed AI)
    "Medium": 0.32,     # 0.32s per tile (balanced AI)
    "Difficult": 0.22,  # 0.22s per tile (fast/agile AI)
    "Hard": 0.16,       # 0.16s per tile (hyper-fast AI)
}

# UI Typography Colors
COLOR_TEXT_WHITE: Tuple[int, int, int] = (248, 250, 252)
COLOR_TEXT_MUTED: Tuple[int, int, int] = (148, 163, 184)
COLOR_TEXT_ACCENT: Tuple[int, int, int] = (56, 189, 248)
COLOR_SUCCESS: Tuple[int, int, int] = (34, 197, 94)
COLOR_WARNING: Tuple[int, int, int] = (249, 115, 22)
COLOR_DANGER: Tuple[int, int, int] = (239, 68, 68)

# Button States
COLOR_BTN_DEFAULT: Tuple[int, int, int] = (30, 41, 59)
COLOR_BTN_HOVER: Tuple[int, int, int] = (51, 65, 85)
COLOR_BTN_ACTIVE: Tuple[int, int, int] = (2, 132, 199)
COLOR_BTN_TEXT: Tuple[int, int, int] = (241, 245, 249)

# Grid Cell Definitions
CELL_WALL: int = 1
CELL_PATH: int = 0

# Collectible Types
ITEM_COIN: str = "coin"
ITEM_GEM: str = "gem"
ITEM_KEY: str = "key"

# Collectible Point Values
POINTS_COIN: int = 50
POINTS_GEM: int = 150
POINTS_KEY: int = 200

# Difficulty Settings - Fixed 25x25 grid for all levels
DIFFICULTY_SETTINGS: Dict[str, Dict[str, Any]] = {
    "Easy": {
        "rows": 25,
        "cols": 25,
        "time_limit": None,  # No strict timer pressure
        "max_hints": 5,
        "hint_cooldown": 3.0,
        "coin_count": 8,
        "gem_count": 4,
        "require_key": False,
        "base_clear_bonus": 500,
        "preview_duration": 4.0,
        "agent_speed": 0.44,
        "badge": "CASUAL",
        "accent": (56, 189, 248),  # Sky cyan
        "description": "Relaxed pace • No timer • Key optional • 5 Hints",
    },
    "Medium": {
        "rows": 25,
        "cols": 25,
        "time_limit": 120,  # 2 minutes
        "max_hints": 3,
        "hint_cooldown": 5.0,
        "coin_count": 12,
        "gem_count": 6,
        "require_key": True,
        "base_clear_bonus": 1000,
        "preview_duration": 4.0,
        "agent_speed": 0.32,
        "badge": "BALANCED",
        "accent": (52, 211, 153),  # Emerald green
        "description": "Timed run (120s) • Golden Key required • 3 Hints",
    },
    "Difficult": {
        "rows": 25,
        "cols": 25,
        "time_limit": 80,   # 80 seconds
        "max_hints": 2,
        "hint_cooldown": 7.0,
        "coin_count": 16,
        "gem_count": 8,
        "require_key": True,
        "base_clear_bonus": 1750,
        "preview_duration": 3.0,
        "agent_speed": 0.22,
        "badge": "EXPERT",
        "accent": (251, 146, 60),  # Amber orange
        "description": "Fast-paced (80s) • Agile AI rival • Key required • 2 Hints",
    },
    "Hard": {
        "rows": 25,
        "cols": 25,
        "time_limit": 50,   # 50 seconds
        "max_hints": 1,
        "hint_cooldown": 10.0,
        "coin_count": 20,
        "gem_count": 10,
        "require_key": True,
        "base_clear_bonus": 2500,
        "preview_duration": 2.0,
        "agent_speed": 0.16,
        "badge": "EXTREME",
        "accent": (244, 63, 94),   # Crimson rose
        "description": "Intense sprint (50s) • Hyper-fast AI • Key required • 1 Hint",
    },
}

DEFAULT_DIFFICULTY: str = "Medium"
MAX_ROWS: int = 35
MAX_COLS: int = 35
