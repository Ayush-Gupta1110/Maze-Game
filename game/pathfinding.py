"""Pathfinding algorithms for Maze Explorer: BFS, DFS, and A*.

Provides standalone route calculation independent of Pygame rendering.
"""

from collections import deque
import heapq
from typing import Dict, List, Optional, Set, Tuple

from config import ITEM_KEY
from game.maze_generator import Maze


def get_neighbors(maze: Maze, r: int, c: int) -> List[Tuple[int, int]]:
    """Return all valid adjacent walkable orthogonal neighbors."""
    neighbors: List[Tuple[int, int]] = []
    # Up, down, left, right
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if maze.is_walkable(nr, nc):
            neighbors.append((nr, nc))
    return neighbors


def reconstruct_path(
    parent_map: Dict[Tuple[int, int], Tuple[int, int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> List[Tuple[int, int]]:
    """Reconstruct path from start to goal using parent pointers."""
    path: List[Tuple[int, int]] = []
    curr: Optional[Tuple[int, int]] = goal
    while curr is not None:
        path.append(curr)
        if curr == start:
            break
        curr = parent_map.get(curr)
    path.reverse()
    return path


def find_path_bfs(
    maze: Maze,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Optional[List[Tuple[int, int]]]:
    """Find the shortest path using Breadth-First Search (BFS).

    Returns:
        List of coordinates from start to goal, or None if unreachable.
    """
    if not maze.is_walkable(start[0], start[1]) or not maze.is_walkable(goal[0], goal[1]):
        return None

    if start == goal:
        return [start]

    queue: deque[Tuple[int, int]] = deque([start])
    visited: Set[Tuple[int, int]] = {start}
    parent: Dict[Tuple[int, int], Tuple[int, int]] = {}

    while queue:
        curr = queue.popleft()
        if curr == goal:
            return reconstruct_path(parent, start, goal)

        for neighbor in get_neighbors(maze, curr[0], curr[1]):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = curr
                queue.append(neighbor)

    return None


def find_path_dfs(
    maze: Maze,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Optional[List[Tuple[int, int]]]:
    """Find a path using Depth-First Search (DFS).

    Returns:
        List of coordinates from start to goal, or None if unreachable.
    """
    if not maze.is_walkable(start[0], start[1]) or not maze.is_walkable(goal[0], goal[1]):
        return None

    if start == goal:
        return [start]

    stack: List[Tuple[int, int]] = [start]
    visited: Set[Tuple[int, int]] = {start}
    parent: Dict[Tuple[int, int], Tuple[int, int]] = {}

    while stack:
        curr = stack.pop()
        if curr == goal:
            return reconstruct_path(parent, start, goal)

        for neighbor in get_neighbors(maze, curr[0], curr[1]):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = curr
                stack.append(neighbor)

    return None


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Calculate Manhattan distance between two grid cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path_astar(
    maze: Maze,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Optional[List[Tuple[int, int]]]:
    """Find the optimal shortest path using A* search.

    Returns:
        List of coordinates from start to goal, or None if unreachable.
    """
    if not maze.is_walkable(start[0], start[1]) or not maze.is_walkable(goal[0], goal[1]):
        return None

    if start == goal:
        return [start]

    # Priority queue stores tuples of (f_score, tie_breaker, (r, c))
    counter: int = 0
    open_set: List[Tuple[int, int, Tuple[int, int]]] = []
    heapq.heappush(open_set, (manhattan_distance(start, goal), counter, start))

    parent: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score: Dict[Tuple[int, int], int] = {start: 0}
    closed_set: Set[Tuple[int, int]] = set()

    while open_set:
        _, _, curr = heapq.heappop(open_set)

        if curr == goal:
            return reconstruct_path(parent, start, goal)

        if curr in closed_set:
            continue
        closed_set.add(curr)

        for neighbor in get_neighbors(maze, curr[0], curr[1]):
            tentative_g = g_score[curr] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f_score = tentative_g + manhattan_distance(neighbor, goal)
                parent[neighbor] = curr
                counter += 1
                heapq.heappush(open_set, (f_score, counter, neighbor))

    return None


def get_hint_route(
    maze: Maze,
    current_pos: Tuple[int, int],
    has_key: bool,
) -> Optional[List[Tuple[int, int]]]:
    """Compute complete route to objective (key first if required, then exit)."""
    # Check if an uncollected key exists in the maze
    key_pos: Optional[Tuple[int, int]] = None
    for pos, item_type in maze.collectibles.items():
        if item_type == ITEM_KEY:
            key_pos = pos
            break

    # If key exists and player doesn't have it, route to key first, then to exit
    if key_pos is not None and not has_key:
        path_to_key = find_path_astar(maze, current_pos, key_pos)
        if not path_to_key:
            return None
        path_to_exit = find_path_astar(maze, key_pos, maze.exit_pos)
        if not path_to_exit:
            return path_to_key
        # Combine paths avoiding duplicate key cell
        return path_to_key + path_to_exit[1:]

    # Otherwise route directly to exit
    return find_path_astar(maze, current_pos, maze.exit_pos)
