"""
Master Procedural Dungeon Generator tying together:
1. BSP Tree partitioning
2. Room carving
3. Kruskal's MST corridor connection
4. Entity placement (Player, Exit, Monster, Treasure)
5. A* verification of dungeon solvability
"""

import random
from typing import List, Tuple, Dict, Any, Optional
from src.bsp_tree import BSPNode, Room
from src.mst import build_mst_corridors, Edge
from src.pathfinding import astar_search, bfs_reachable_tiles


class Tile:
    WALL = 0
    FLOOR = 1
    CORRIDOR = 2
    DOOR = 3
    ENTRANCE = 4
    EXIT = 5
    TREASURE = 6
    MONSTER = 7


TILE_CHARS = {
    Tile.WALL: "█",
    Tile.FLOOR: ".",
    Tile.CORRIDOR: "░",
    Tile.DOOR: "+",
    Tile.ENTRANCE: "@",
    Tile.EXIT: ">",
    Tile.TREASURE: "$",
    Tile.MONSTER: "M",
}


class DungeonGenerator:
    def __init__(
        self,
        width: int = 60,
        height: int = 35,
        min_room_size: int = 5,
        max_bsp_depth: int = 4,
        extra_loops_ratio: float = 0.15,
    ):
        self.width = width
        self.height = height
        self.min_room_size = min_room_size
        self.max_bsp_depth = max_bsp_depth
        self.extra_loops_ratio = extra_loops_ratio

        self.grid: List[List[int]] = [[Tile.WALL for _ in range(width)] for _ in range(height)]
        self.rooms: List[Room] = []
        self.mst_edges: List[Edge] = []
        self.extra_edges: List[Edge] = []
        self.bsp_root: Optional[BSPNode] = None

        self.player_pos: Tuple[int, int] = (0, 0)
        self.exit_pos: Tuple[int, int] = (0, 0)
        self.treasures: List[Tuple[int, int]] = []
        self.monsters: List[Tuple[int, int]] = []

    def generate(self) -> Dict[str, Any]:
        """Runs complete generation pipeline."""
        # 1. Reset Grid
        self.grid = [[Tile.WALL for _ in range(self.width)] for _ in range(self.height)]

        # 2. Build BSP Tree
        self.bsp_root = BSPNode(0, 0, self.width, self.height, depth=0)
        self.bsp_root.build_tree(max_depth=self.max_bsp_depth, min_size=self.min_room_size + 2)

        # 3. Carve Rooms in leaf partitions
        self.rooms = self.bsp_root.create_rooms(
            min_room_size=self.min_room_size, padding=1
        )

        for room in self.rooms:
            self._carve_room(room)

        # 4. Connect rooms with Kruskal's MST
        self.mst_edges, self.extra_edges = build_mst_corridors(
            self.rooms, extra_loop_chance=self.extra_loops_ratio
        )

        all_corridors = self.mst_edges + self.extra_edges
        for edge in all_corridors:
            r1 = self.rooms[edge.u]
            r2 = self.rooms[edge.v]
            self._carve_corridor(r1.center, r2.center)

        # 5. Place Entities (Player, Exit, Treasures, Monsters)
        if len(self.rooms) >= 2:
            # Player starts in Room 0
            self.player_pos = self.rooms[0].center
            # Exit is placed in the farthest room from Room 0
            farthest_room = max(
                self.rooms[1:],
                key=lambda r: (r.center[0] - self.player_pos[0]) ** 2 + (r.center[1] - self.player_pos[1]) ** 2,
            )
            self.exit_pos = farthest_room.center
        elif self.rooms:
            self.player_pos = self.rooms[0].center
            self.exit_pos = (self.rooms[0].x + 1, self.rooms[0].y + 1)

        # Scatter treasures & monsters in other rooms
        self.treasures = []
        self.monsters = []
        for i, room in enumerate(self.rooms):
            if room.center not in [self.player_pos, self.exit_pos]:
                # 60% chance of treasure
                if random.random() < 0.6:
                    tx = random.randint(room.x + 1, room.x + room.width - 2)
                    ty = random.randint(room.y + 1, room.y + room.height - 2)
                    self.treasures.append((tx, ty))
                # 40% chance of monster
                if random.random() < 0.4:
                    mx = random.randint(room.x + 1, room.x + room.width - 2)
                    my = random.randint(room.y + 1, room.y + room.height - 2)
                    if (mx, my) not in self.treasures:
                        self.monsters.append((mx, my))

        # 6. Verify Solvability with A* Search
        solvable_path = astar_search(
            self.grid, self.player_pos, self.exit_pos, walkable_values={Tile.FLOOR, Tile.CORRIDOR}
        )

        return {
            "rooms_count": len(self.rooms),
            "mst_edges_count": len(self.mst_edges),
            "extra_loops_count": len(self.extra_edges),
            "is_solvable": solvable_path is not None,
            "optimal_path_length": len(solvable_path) if solvable_path else 0,
            "solvable_path": solvable_path or [],
        }

    def _carve_room(self, room: Room):
        """Carve floor tiles for a given room."""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= y < self.height and 0 <= x < self.width:
                    self.grid[y][x] = Tile.FLOOR

    def _carve_corridor(self, p1: Tuple[int, int], p2: Tuple[int, int]):
        """Carves an L-shaped corridor connecting two points."""
        x1, y1 = p1
        x2, y2 = p2

        # 50% chance horizontal first, or vertical first
        if random.random() < 0.5:
            self._carve_h_corridor(x1, x2, y1)
            self._carve_v_corridor(y1, y2, x2)
        else:
            self._carve_v_corridor(y1, y2, x1)
            self._carve_h_corridor(x1, x2, y2)

    def _carve_h_corridor(self, x1: int, x2: int, y: int):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= y < self.height and 0 <= x < self.width:
                if self.grid[y][x] == Tile.WALL:
                    self.grid[y][x] = Tile.CORRIDOR

    def _carve_v_corridor(self, y1: int, y2: int, x: int):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= y < self.height and 0 <= x < self.width:
                if self.grid[y][x] == Tile.WALL:
                    self.grid[y][x] = Tile.CORRIDOR

    def render_ascii(self, show_path: bool = False, path_coords: Optional[List[Tuple[int, int]]] = None) -> str:
        """Renders dungeon to human-readable ASCII string."""
        path_set = set(path_coords) if (show_path and path_coords) else set()
        treasure_set = set(self.treasures)
        monster_set = set(self.monsters)

        lines = []
        for y in range(self.height):
            row_chars = []
            for x in range(self.width):
                coord = (x, y)
                if coord == self.player_pos:
                    row_chars.append("@")
                elif coord == self.exit_pos:
                    row_chars.append(">")
                elif coord in monster_set:
                    row_chars.append("M")
                elif coord in treasure_set:
                    row_chars.append("$")
                elif coord in path_set:
                    row_chars.append("*")  # A* shortest path indicator
                else:
                    row_chars.append(TILE_CHARS.get(self.grid[y][x], " "))
            lines.append("".join(row_chars))
        return "\n".join(lines)
