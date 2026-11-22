"""
Binary Space Partitioning (BSP) Tree for Procedural Room Generation.

Time Complexity: O(N log N) recursive space partitioning
Space Complexity: O(N) for tree nodes
"""

import random
from typing import Optional, List, Tuple


class Room:
    def __init__(self, room_id: int, x: int, y: int, width: int, height: int):
        self.id = room_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def center(self) -> Tuple[int, int]:
        """Calculates center coordinate (x, y) of the room."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def overlaps(self, other: "Room", padding: int = 1) -> bool:
        """Check if this room overlaps with another room (with margin)."""
        return not (
            self.x + self.width + padding <= other.x
            or other.x + other.width + padding <= self.x
            or self.y + self.height + padding <= other.y
            or other.y + other.height + padding <= self.y
        )

    def __repr__(self):
        return f"Room(id={self.id}, x={self.x}, y={self.y}, w={self.width}, h={self.height})"


class BSPNode:
    """A node representing a rectangular region in the 2D dungeon grid."""

    def __init__(self, x: int, y: int, width: int, height: int, depth: int = 0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.depth = depth

        self.left: Optional[BSPNode] = None
        self.right: Optional[BSPNode] = None
        self.room: Optional[Room] = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def split(self, min_size: int = 8) -> bool:
        """
        Recursively splits region horizontally or vertically into two sub-regions.
        Returns True if successfully split, False if too small.
        """
        if not self.is_leaf:
            return False

        # If too small to split into two valid sub-partitions
        if self.width < min_size * 2 and self.height < min_size * 2:
            return False

        # Determine split direction
        # Favor splitting the longer dimension to keep rooms square-ish
        if self.width / max(1, self.height) >= 1.25:
            split_horizontally = False  # Split vertically (cut X axis)
        elif self.height / max(1, self.width) >= 1.25:
            split_horizontally = True   # Split horizontally (cut Y axis)
        else:
            split_horizontally = random.choice([True, False])

        max_split = (self.height if split_horizontally else self.width) - min_size
        if max_split <= min_size:
            return False

        # Split between 40% and 60% of the dimension
        split_pos = random.randint(min_size, max_split)

        if split_horizontally:
            self.left = BSPNode(self.x, self.y, self.width, split_pos, self.depth + 1)
            self.right = BSPNode(self.x, self.y + split_pos, self.width, self.height - split_pos, self.depth + 1)
        else:
            self.left = BSPNode(self.x, self.y, split_pos, self.height, self.depth + 1)
            self.right = BSPNode(self.x + split_pos, self.y, self.width - split_pos, self.height, self.depth + 1)

        return True

    def build_tree(self, max_depth: int = 4, min_size: int = 8):
        """Recursively splits nodes until max_depth or minimum size is reached."""
        if self.depth >= max_depth:
            return

        if self.split(min_size):
            if self.left:
                self.left.build_tree(max_depth, min_size)
            if self.right:
                self.right.build_tree(max_depth, min_size)

    def create_rooms(self, min_room_size: int = 4, padding: int = 1, room_counter: List[int] = None) -> List[Room]:
        """
        Carves random rooms inside leaf partitions with padding.
        Returns a list of all created Room instances.
        """
        if room_counter is None:
            room_counter = [0]

        rooms: List[Room] = []

        if self.is_leaf:
            # Maximum allowed room dimensions inside this partition
            max_w = self.width - 2 * padding
            max_h = self.height - 2 * padding

            if max_w >= min_room_size and max_h >= min_room_size:
                room_w = random.randint(min_room_size, max_w)
                room_h = random.randint(min_room_size, max_h)
                room_x = self.x + padding + random.randint(0, max_w - room_w)
                room_y = self.y + padding + random.randint(0, max_h - room_h)

                self.room = Room(room_counter[0], room_x, room_y, room_w, room_h)
                room_counter[0] += 1
                rooms.append(self.room)
        else:
            if self.left:
                rooms.extend(self.left.create_rooms(min_room_size, padding, room_counter))
            if self.right:
                rooms.extend(self.right.create_rooms(min_room_size, padding, room_counter))

        return rooms
