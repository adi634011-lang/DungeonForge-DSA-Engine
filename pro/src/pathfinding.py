"""
A* Search and BFS Pathfinding Algorithms.
Used for Player-to-Goal shortest route and Monster AI navigation.

Data Structures:
- Min-Heap / Priority Queue (heapq)
- Hash Map for cost tracking (g_score, f_score)
- Queue (collections.deque) for BFS

Time Complexity:
- A*: O(E) = O(V log V) with Min-Heap
- BFS: O(V + E)
"""

import heapq
from collections import deque
from typing import List, Tuple, Dict, Optional, Set


def manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    """Manhattan heuristic: h(x, y) = |x1 - x2| + |y1 - y2|"""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def astar_search(
    grid: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    walkable_values: Set[int] = {1, 2, 3, 4}
) -> Optional[List[Tuple[int, int]]]:
    """
    A* Shortest Pathfinding on 2D grid.

    Args:
        grid: 2D matrix where walkable values are defined by walkable_values set.
        start: (x, y) coordinate
        goal: (x, y) coordinate
        walkable_values: Set of grid values considered passable (e.g. floor=1, corridor=2)

    Returns:
        List of (x, y) coordinates from start to goal, or None if no path exists.
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    if not (0 <= start[1] < height and 0 <= start[0] < width):
        return None
    if not (0 <= goal[1] < height and 0 <= goal[0] < width):
        return None

    # Priority queue holds entries: (f_score, counter, (x, y))
    # counter breaks ties cleanly without comparing coordinate tuples
    counter = 0
    open_heap = []
    heapq.heappush(open_heap, (manhattan_distance(start, goal), counter, start))

    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score: Dict[Tuple[int, int], float] = {start: 0.0}
    f_score: Dict[Tuple[int, int], float] = {start: float(manhattan_distance(start, goal))}
    closed_set: Set[Tuple[int, int]] = set()

    # 4-directional movement (orthogonal)
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while open_heap:
        current_f, _, current = heapq.heappop(open_heap)

        if current == goal:
            # Reconstruct path from goal back to start
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        closed_set.add(current)

        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            nx, ny = neighbor

            # Check grid boundaries
            if not (0 <= nx < width and 0 <= ny < height):
                continue

            # Passable terrain check
            if grid[ny][nx] not in walkable_values:
                continue

            if neighbor in closed_set:
                continue

            tentative_g = g_score[current] + 1.0

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + manhattan_distance(neighbor, goal)
                f_score[neighbor] = f
                counter += 1
                heapq.heappush(open_heap, (f, counter, neighbor))

    return None  # No path found


def bfs_reachable_tiles(
    grid: List[List[int]],
    start: Tuple[int, int],
    walkable_values: Set[int] = {1, 2, 3, 4}
) -> Set[Tuple[int, int]]:
    """BFS flood-fill to get all reachable floor coordinates."""
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    visited: Set[Tuple[int, int]] = {start}
    queue = deque([start])
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while queue:
        cx, cy = queue.popleft()
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                if grid[ny][nx] in walkable_values and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

    return visited
