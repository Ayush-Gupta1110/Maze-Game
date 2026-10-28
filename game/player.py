"""Player character logic, movement validation, and inventory tracking."""

from typing import Optional, Tuple

from config import (
    ITEM_COIN,
    ITEM_GEM,
    ITEM_KEY,
    POINTS_COIN,
    POINTS_GEM,
    POINTS_KEY,
)
from game.maze_generator import Maze


class Player:
    """Represents the player navigating the maze."""

    def __init__(self, start_pos: Tuple[int, int], max_hints: int = 3) -> None:
        """Initialize player at start position."""
        self.row: int = start_pos[0]
        self.col: int = start_pos[1]
        self.start_pos: Tuple[int, int] = start_pos

        # Visual interpolation coordinates (in grid units)
        self.visual_row: float = float(self.row)
        self.visual_col: float = float(self.col)

        # Facing direction (dr, dc)
        self.facing: Tuple[int, int] = (0, 1)

        # Gameplay statistics
        self.moves_count: int = 0
        self.score: int = 0
        self.coins_collected: int = 0
        self.gems_collected: int = 0
        self.has_key: bool = False

        # Hint management
        self.hints_remaining: int = max_hints
        self.last_hint_time: float = -999.0

    @property
    def pos(self) -> Tuple[int, int]:
        """Return current grid position tuple (row, col)."""
        return (self.row, self.col)

    def move(self, dr: int, dc: int, maze: Maze) -> bool:
        """Attempt to move by delta (dr, dc).

        Returns:
            True if movement was valid and executed, False if blocked by a wall or boundary.
        """
        if dr == 0 and dc == 0:
            return False

        # Update facing direction regardless of collision
        self.facing = (dr, dc)

        target_r = self.row + dr
        target_c = self.col + dc

        if maze.is_walkable(target_r, target_c):
            self.row = target_r
            self.col = target_c
            self.moves_count += 1
            return True

        return False

    def update_visual_pos(self, lerp_speed: float = 0.35) -> None:
        """Smoothly interpolate visual coordinates toward grid coordinates."""
        self.visual_row += (self.row - self.visual_row) * lerp_speed
        self.visual_col += (self.col - self.visual_col) * lerp_speed

    def check_collectibles(self, maze: Maze) -> Optional[str]:
        """Check if player is standing on a collectible, collect it, and update score.

        Returns:
            Item type collected (e.g. 'coin', 'gem', 'key'), or None.
        """
        item_type = maze.remove_collectible(self.pos)
        if item_type is None:
            return None

        if item_type == ITEM_COIN:
            self.coins_collected += 1
            self.score += POINTS_COIN
        elif item_type == ITEM_GEM:
            self.gems_collected += 1
            self.score += POINTS_GEM
        elif item_type == ITEM_KEY:
            self.has_key = True
            self.score += POINTS_KEY

        return item_type

    def reset_position(self, start_pos: Optional[Tuple[int, int]] = None) -> None:
        """Reset player coordinates back to start without wiping overall game progress."""
        if start_pos is not None:
            self.start_pos = start_pos
        self.row, self.col = self.start_pos
        self.visual_row, self.visual_col = float(self.row), float(self.col)
        self.facing = (0, 1)
