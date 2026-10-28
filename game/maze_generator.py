"""Procedural maze generator using recursive backtracking.

Decoupled from Pygame rendering for standalone testing and headless execution.
"""

import random
from typing import Dict, List, Optional, Set, Tuple

from config import (
    CELL_PATH,
    CELL_WALL,
    ITEM_COIN,
    ITEM_GEM,
    ITEM_KEY,
)


class Maze:
    """Represents a 2D maze with entrance, exit, and placed collectibles."""

    def __init__(
        self,
        rows: int,
        cols: int,
        seed: Optional[int] = None,
        coin_count: int = 5,
        gem_count: int = 2,
        require_key: bool = False,
        loop_factor: float = 0.05,
    ) -> None:
        """Initialize and generate a connected maze.

        Args:
            rows: Total height of the grid (adjusted to odd number if even).
            cols: Total width of the grid (adjusted to odd number if even).
            seed: Optional random seed for reproducible generation.
            coin_count: Number of coins to place.
            gem_count: Number of gems to place.
            require_key: Whether a key is placed in the maze.
            loop_factor: Ratio of dead ends to open up into loops (0.0 to 0.2).
        """
        # Ensure dimensions are odd to maintain proper grid corridors and walls
        self.rows: int = rows if rows % 2 != 0 else rows + 1
        self.cols: int = cols if cols % 2 != 0 else cols + 1
        self.seed: Optional[int] = seed
        self.rng: random.Random = random.Random(seed)

        self.start_pos: Tuple[int, int] = (1, 1)
        self.exit_pos: Tuple[int, int] = (self.rows - 2, self.cols - 2)

        # Initialize grid with all walls
        self.grid: List[List[int]] = [
            [CELL_WALL for _ in range(self.cols)] for _ in range(self.rows)
        ]

        # Generate maze layout
        self._generate_maze()

        # Optionally add a few loops for more interesting alternate routes
        if loop_factor > 0:
            self._add_loops(loop_factor)

        # Place collectibles on walkable path cells
        self.collectibles: Dict[Tuple[int, int], str] = {}
        self._place_collectibles(
            coin_count=coin_count,
            gem_count=gem_count,
            require_key=require_key,
        )

    def _generate_maze(self) -> None:
        """Carve maze passages using the recursive backtracking algorithm."""
        start_r, start_c = self.start_pos
        self.grid[start_r][start_c] = CELL_PATH

        stack: List[Tuple[int, int]] = [(start_r, start_c)]
        visited: Set[Tuple[int, int]] = {(start_r, start_c)}

        # Cardinal movement directions by 2 steps
        directions: List[Tuple[int, int]] = [(-2, 0), (2, 0), (0, -2), (0, 2)]

        while stack:
            curr_r, curr_c = stack[-1]

            # Find unvisited 2-step neighbors
            unvisited_neighbors: List[Tuple[int, int, int, int]] = []
            for dr, dc in directions:
                nr, nc = curr_r + dr, curr_c + dc
                if 1 <= nr < self.rows - 1 and 1 <= nc < self.cols - 1:
                    if (nr, nc) not in visited:
                        wall_r = curr_r + dr // 2
                        wall_c = curr_c + dc // 2
                        unvisited_neighbors.append((nr, nc, wall_r, wall_c))

            if unvisited_neighbors:
                # Choose one neighbor randomly using our seeded generator
                nr, nc, wr, wc = self.rng.choice(unvisited_neighbors)
                # Carve wall and destination cell
                self.grid[wr][wc] = CELL_PATH
                self.grid[nr][nc] = CELL_PATH
                visited.add((nr, nc))
                stack.append((nr, nc))
            else:
                stack.pop()

        # Ensure exit cell is open
        exit_r, exit_c = self.exit_pos
        self.grid[exit_r][exit_c] = CELL_PATH

    def _add_loops(self, loop_factor: float) -> None:
        """Remove a small percentage of walls to introduce alternate paths and loops."""
        inner_walls: List[Tuple[int, int]] = []
        for r in range(2, self.rows - 2, 2):
            for c in range(1, self.cols - 1, 2):
                if self.grid[r][c] == CELL_WALL:
                    if self.grid[r - 1][c] == CELL_PATH and self.grid[r + 1][c] == CELL_PATH:
                        inner_walls.append((r, c))

        for r in range(1, self.rows - 1, 2):
            for c in range(2, self.cols - 2, 2):
                if self.grid[r][c] == CELL_WALL:
                    if self.grid[r][c - 1] == CELL_PATH and self.grid[r][c + 1] == CELL_PATH:
                        inner_walls.append((r, c))

        self.rng.shuffle(inner_walls)
        walls_to_remove = int(len(inner_walls) * max(0.0, min(loop_factor, 0.25)))
        for i in range(walls_to_remove):
            wr, wc = inner_walls[i]
            self.grid[wr][wc] = CELL_PATH

    def _place_collectibles(
        self,
        coin_count: int,
        gem_count: int,
        require_key: bool,
    ) -> None:
        """Place coins, gems, and optional key onto distinct walkable cells."""
        walkable = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if self.grid[r][c] == CELL_PATH
            and (r, c) != self.start_pos
            and (r, c) != self.exit_pos
        ]

        if not walkable:
            return

        self.rng.shuffle(walkable)

        # Place key if required, preferably somewhere strategically distant from start
        if require_key and walkable:
            # Sort a sample of candidates by distance to start, pick one far away
            best_key_pos = max(
                walkable[: min(len(walkable), 20)],
                key=lambda pos: abs(pos[0] - self.start_pos[0]) + abs(pos[1] - self.start_pos[1]),
            )
            self.collectibles[best_key_pos] = ITEM_KEY
            walkable.remove(best_key_pos)

        # Place coins
        num_coins = min(coin_count, len(walkable))
        for _ in range(num_coins):
            pos = walkable.pop()
            self.collectibles[pos] = ITEM_COIN

        # Place gems
        num_gems = min(gem_count, len(walkable))
        for _ in range(num_gems):
            pos = walkable.pop()
            self.collectibles[pos] = ITEM_GEM

    def is_valid_coord(self, row: int, col: int) -> bool:
        """Check if coordinates fall within grid bounds."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_walkable(self, row: int, col: int) -> bool:
        """Check if cell is within bounds and not a wall."""
        return self.is_valid_coord(row, col) and self.grid[row][col] == CELL_PATH

    def get_walkable_cells(self) -> List[Tuple[int, int]]:
        """Return list of all walkable coordinate tuples."""
        return [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if self.grid[r][c] == CELL_PATH
        ]

    def remove_collectible(self, pos: Tuple[int, int]) -> Optional[str]:
        """Remove and return collectible at given position, or None if empty."""
        return self.collectibles.pop(pos, None)
