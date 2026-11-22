"""
Unit Tests for DSA Components:
1. Disjoint Set Union (Union-Find)
2. BSP Tree Partitioning
3. Kruskal's Minimum Spanning Tree
4. A* Search Shortest Pathfinding
"""

import unittest
from src.dsu import DisjointSetUnion
from src.bsp_tree import BSPNode, Room
from src.mst import build_mst_corridors, calculate_distance
from src.pathfinding import astar_search, manhattan_distance
from src.dungeon_generator import DungeonGenerator, Tile


class TestDSAComponents(unittest.TestCase):

    def test_dsu_union_find(self):
        dsu = DisjointSetUnion(5)
        self.assertEqual(dsu.num_sets, 5)

        # Merge 0 and 1
        self.assertTrue(dsu.union(0, 1))
        self.assertTrue(dsu.connected(0, 1))
        self.assertEqual(dsu.num_sets, 4)

        # Redundant union should return False (cycle detection)
        self.assertFalse(dsu.union(0, 1))
        self.assertEqual(dsu.num_sets, 4)

        # Merge 2 and 3, then 1 and 2
        dsu.union(2, 3)
        dsu.union(1, 2)
        self.assertTrue(dsu.connected(0, 3))
        self.assertFalse(dsu.connected(0, 4))

    def test_bsp_tree_splits(self):
        root = BSPNode(0, 0, 40, 40)
        root.build_tree(max_depth=3, min_size=8)
        rooms = root.create_rooms(min_room_size=4, padding=1)

        self.assertGreater(len(rooms), 0)
        # Verify rooms are within bounds
        for r in rooms:
            self.assertGreaterEqual(r.x, 0)
            self.assertGreaterEqual(r.y, 0)
            self.assertLessEqual(r.x + r.width, 40)
            self.assertLessEqual(r.y + r.height, 40)

    def test_kruskal_mst(self):
        # 3 rooms in a triangle
        r0 = Room(0, 0, 0, 4, 4)
        r1 = Room(1, 10, 0, 4, 4)
        r2 = Room(2, 0, 10, 4, 4)

        mst_edges, _ = build_mst_corridors([r0, r1, r2], extra_loop_chance=0.0)
        # An MST for 3 vertices must have exactly 2 edges
        self.assertEqual(len(mst_edges), 2)

    def test_astar_search(self):
        # 5x5 grid: open floor with an obstacle
        grid = [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 0, 1],
            [0, 0, 1, 0, 1],
            [1, 1, 1, 1, 1],
        ]
        start = (0, 0)
        goal = (4, 4)
        path = astar_search(grid, start, goal, walkable_values={1})

        self.assertIsNotNone(path)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)

    def test_dungeon_generator_solvability(self):
        # Run 10 generations, all should guarantee connectivity and solvability
        for _ in range(10):
            dg = DungeonGenerator(width=40, height=25, min_room_size=4, max_bsp_depth=3)
            stats = dg.generate()
            if stats["rooms_count"] > 1:
                self.assertTrue(stats["is_solvable"], "Generated dungeon should be 100% solvable via MST corridors")


if __name__ == "__main__":
    unittest.main()
