"""AI Agent competitor using A* pathfinding for Maze Explorer."""

import time
from typing import List, Optional, Tuple

from config import AGENT_STEP_SPEEDS, ITEM_KEY
from game.maze_generator import Maze
from game.pathfinding import get_hint_route


class Agent:
    """Represents the AI rival that navigates the maze using the A* algorithm."""

    def __init__(
        self,
        start_pos: Tuple[int, int],
        difficulty: str = "Medium",
        step_interval: Optional[float] = None,
    ) -> None:
        """Initialize AI agent at starting position."""
        self.row: int = start_pos[0]
        self.col: int = start_pos[1]
        self.start_pos: Tuple[int, int] = start_pos

        # Visual smooth interpolation
        self.visual_row: float = float(self.row)
        self.visual_col: float = float(self.col)

        # Facing direction (dr, dc)
        self.facing: Tuple[int, int] = (0, 1)

        # A* Path coordinates
        self.path: List[Tuple[int, int]] = []
        self.path_index: int = 0

        # Step timing
        self.difficulty: str = difficulty
        if step_interval is not None:
            self.step_interval: float = float(step_interval)
        else:
            self.step_interval = AGENT_STEP_SPEEDS.get(difficulty, 0.32)
        self.step_timer: float = 0.0

        # Status
        self.has_key: bool = False
        self.finished: bool = False
        self.moves_count: int = 0
        self.total_path_length: int = 0

        # Visual trail for glowing effect: list of (visual_row, visual_col, timestamp)
        self.trail: List[Tuple[float, float, float]] = []

    @property
    def pos(self) -> Tuple[int, int]:
        """Current grid cell tuple."""
        return (self.row, self.col)

    def calculate_path(self, maze: Maze) -> bool:
        """Compute complete route to objective using A* (key first if required, then exit)."""
        route = get_hint_route(maze, self.pos, self.has_key)
        if route and len(route) > 0:
            self.path = route
            self.path_index = 0
            self.total_path_length = len(route)
            return True
        return False

    def remaining_distance(self) -> int:
        """Return number of steps remaining until the exit."""
        if not self.path:
            return 0
        return max(0, len(self.path) - 1 - self.path_index)

    def progress(self) -> float:
        """Return completion ratio between 0.0 and 1.0."""
        if self.total_path_length <= 1:
            return 1.0 if self.finished else 0.0
        return min(1.0, self.path_index / max(1, self.total_path_length - 1))

    def update(self, dt: float, maze: Maze) -> bool:
        """Take a step along the A* route if the step interval has elapsed.

        Returns:
            True if the agent took a step this frame.
        """
        if self.finished or not self.path:
            return False

        if self.path_index >= len(self.path) - 1:
            self.finished = True
            return False

        self.step_timer += dt
        if self.step_timer < self.step_interval:
            return False

        # Reset accumulator for next interval
        self.step_timer -= self.step_interval
        next_step = self.path[self.path_index + 1]

        # Update facing
        dr = next_step[0] - self.row
        dc = next_step[1] - self.col
        self.facing = (dr, dc)

        # Move to next cell
        self.row = next_step[0]
        self.col = next_step[1]
        self.path_index += 1
        self.moves_count += 1

        # Check if agent collects key if passing through key position
        if maze.collectibles.get(self.pos) == ITEM_KEY:
            self.has_key = True

        # Check if reached exit
        if self.pos == maze.exit_pos:
            self.finished = True

        return True

    def update_visual_pos(self, lerp_speed: float = 0.35) -> None:
        """Smoothly interpolate visual coordinates toward grid coordinates and record trail."""
        self.visual_row += (self.row - self.visual_row) * lerp_speed
        self.visual_col += (self.col - self.visual_col) * lerp_speed

        now = time.time()
        self.trail.append((self.visual_row, self.visual_col, now))
        # Keep trail fresh (last 0.8 seconds)
        self.trail = [t for t in self.trail if (now - t[2]) < 0.8]

    def reset(self, start_pos: Optional[Tuple[int, int]] = None, difficulty: Optional[str] = None) -> None:
        """Reset agent to starting state."""
        if start_pos is not None:
            self.start_pos = start_pos
        if difficulty is not None:
            self.difficulty = difficulty
            self.step_interval = AGENT_STEP_SPEEDS.get(difficulty, 0.32)

        self.row, self.col = self.start_pos
        self.visual_row, self.visual_col = float(self.row), float(self.col)
        self.facing = (0, 1)
        self.path = []
        self.path_index = 0
        self.step_timer = 0.0
        self.finished = False
        self.has_key = False
        self.moves_count = 0
        self.trail = []
