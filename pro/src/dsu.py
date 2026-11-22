"""
Disjoint Set Union (DSU) / Union-Find with:
1. Path Compression
2. Union by Rank

Time Complexity: Nearly O(1) amortized per operation (O(alpha(N)) where alpha is inverse Ackermann)
Space Complexity: O(N)
"""

class DisjointSetUnion:
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size
        self.num_sets = size

    def find(self, i: int) -> int:
        """Find the representative/root of the set containing element i with path compression."""
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        """
        Unites the set containing i and the set containing j using union by rank.
        Returns True if sets were disjoint and merged; False if already in same set (cycle detected).
        """
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i == root_j:
            return False  # Already in same set (would create cycle)

        # Union by rank
        if self.rank[root_i] < self.rank[root_j]:
            self.parent[root_i] = root_j
        elif self.rank[root_i] > self.rank[root_j]:
            self.parent[root_j] = root_i
        else:
            self.parent[root_j] = root_i
            self.rank[root_i] += 1

        self.num_sets -= 1
        return True

    def connected(self, i: int, j: int) -> bool:
        """Check if i and j are in the same set."""
        return self.find(i) == self.find(j)
