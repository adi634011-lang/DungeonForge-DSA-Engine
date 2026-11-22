"""
Interactive CLI Runner & Game for Procedural Dungeon Generator.
"""

import os
import sys
import time

# Ensure src can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.dungeon_generator import DungeonGenerator, Tile
from src.pathfinding import astar_search


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def benchmark_dungeon_generation(num_runs: int = 50):
    print(f"\n⚡ Running benchmark over {num_runs} procedural dungeon generations...")
    start_time = time.time()
    solvable_count = 0
    total_rooms = 0
    total_path_length = 0

    for _ in range(num_runs):
        dg = DungeonGenerator(width=50, height=25, min_room_size=4, max_bsp_depth=4)
        stats = dg.generate()
        if stats["is_solvable"]:
            solvable_count += 1
            total_path_length += stats["optimal_path_length"]
        total_rooms += stats["rooms_count"]

    elapsed = time.time() - start_time
    avg_time_ms = (elapsed / num_runs) * 1000

    print(f"✅ Completed {num_runs} runs in {elapsed:.3f}s (Avg: {avg_time_ms:.2f} ms per generation)")
    print(f"📊 Full Solvability Rate (A* Route Exists): {solvable_count}/{num_runs} ({(solvable_count/num_runs)*100:.1f}%)")
    print(f"📊 Average Rooms Per Dungeon: {total_rooms / num_runs:.1f}")
    if solvable_count > 0:
        print(f"📊 Average Optimal Path Length: {total_path_length / solvable_count:.1f} steps")


def main():
    print("=" * 60)
    print("   🎮 PROCEDURAL DUNGEON & MAZE GENERATOR (DSA ENGINE)   ")
    print("=" * 60)

    dg = DungeonGenerator(width=55, height=25, min_room_size=5, max_bsp_depth=4)
    stats = dg.generate()
    show_path = False

    while True:
        clear_screen()
        print("=" * 60)
        print("   🎮 PROCEDURAL DUNGEON GENERATOR (BSP + MST + A*)   ")
        print("=" * 60)
        print(f"🏠 Rooms Carved: {stats['rooms_count']} | 🔗 MST Edges: {stats['mst_edges_count']} | 🔄 Loops: {stats['extra_loops_count']}")
        print(f"🎯 Solvable: {'YES ✅' if stats['is_solvable'] else 'NO ❌'} | 📏 Shortest Path: {stats['optimal_path_length']} tiles")
        print("-" * 60)

        print(dg.render_ascii(show_path=show_path, path_coords=stats["solvable_path"]))

        print("-" * 60)
        print("Legend: @:Player | >:Exit | $:Treasure | M:Monster | *:A* Path | ░:Corridor")
        print("Controls:")
        print("  [G] Generate New Dungeon     [P] Toggle A* Optimal Path")
        print("  [B] Run 50x Benchmark        [Q] Exit to Menu")
        
        choice = input("\nEnter command: ").strip().lower()

        if choice == "g":
            stats = dg.generate()
        elif choice == "p":
            show_path = not show_path
        elif choice == "b":
            benchmark_dungeon_generation()
            input("\nPress Enter to continue...")
        elif choice == "q":
            print("Exiting. Thanks for playing!")
            break


if __name__ == "__main__":
    main()
