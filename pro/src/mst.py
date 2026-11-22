"""
Kruskal's Algorithm for Minimum Spanning Tree (MST).
Connects all rooms with minimal corridor distance and avoids isolated rooms.

Data Structures:
- Disjoint Set Union (Union-Find) with path compression and rank
- Priority Edge Sorting

Time Complexity: O(E log E) where E is number of edges
Space Complexity: O(V + E)
"""

import math
import random
from typing import List, Tuple
from src.dsu import DisjointSetUnion
from src.bsp_tree import Room


class Edge:
    def __init__(self, u: int, v: int, weight: float):
        self.u = u
        self.v = v
        self.weight = weight

    def __lt__(self, other: "Edge"):
        return self.weight < other.weight

    def __repr__(self):
        return f"Edge({self.u} <-> {self.v}, weight={self.weight:.2f})"


def calculate_distance(r1: Room, r2: Room) -> float:
    """Euclidean distance between two room centers."""
    c1 = r1.center
    c2 = r2.center
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1])


def build_mst_corridors(
    rooms: List[Room], extra_loop_chance: float = 0.15
) -> Tuple[List[Edge], List[Edge]]:
    """
    Connects rooms using Kruskal's Algorithm to guarantee full connectivity.
    Optionally re-adds a percentage of non-tree edges to introduce loops.

    Returns:
        (mst_edges, extra_loop_edges)
    """
    n = len(rooms)
    if n <= 1:
        return [], []

    # 1. Generate all pairwise edges between rooms
    edges: List[Edge] = []
    for i in range(n):
        for j in range(i + 1, n):
            dist = calculate_distance(rooms[i], rooms[j])
            edges.append(Edge(i, j, dist))

    # 2. Sort edges by ascending weight: O(E log E)
    edges.sort()

    # 3. Kruskal's Algorithm using DSU
    dsu = DisjointSetUnion(n)
    mst_edges: List[Edge] = []
    unused_edges: List[Edge] = []

    for edge in edges:
        # If edge connects two previously disconnected components, accept it
        if dsu.union(edge.u, edge.v):
            mst_edges.append(edge)
        else:
            unused_edges.append(edge)

    # 4. Add a few extra edges (loops) to make dungeon gameplay less linear
    extra_edges: List[Edge] = []
    for edge in unused_edges:
        if random.random() < extra_loop_chance:
            extra_edges.append(edge)

    return mst_edges, extra_edges
