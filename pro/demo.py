from src.dungeon_generator import DungeonGenerator

def run_demo():
    dg = DungeonGenerator(width=58, height=22, min_room_size=4, max_bsp_depth=4)
    stats = dg.generate()
    print("\n" + "=" * 58)
    print("      ⚔️  DUNGEONFORGE: PROCEDURAL LEVEL GENERATOR  ⚔️")
    print("=" * 58)
    print(dg.render_ascii(show_path=True, path_coords=stats['solvable_path']))
    print("=" * 58)
    print(f"🏠 Rooms Carved : {stats['rooms_count']} rooms")
    print(f"🔗 MST Edges    : {stats['mst_edges_count']} connections (Kruskal's Algorithm)")
    print(f"🔄 Extra Loops  : {stats['extra_loops_count']} cycles added")
    print(f"🎯 Solvability  : {'100% SOLVABLE ✅' if stats['is_solvable'] else 'FAILED ❌'}")
    print(f"📏 A* Path Len  : {stats['optimal_path_length']} steps (shown with '*')")
    print("=" * 58)
    print("Legend: @:Player | >:Exit | $:Treasure | M:Monster | *:Shortest Path\n")

if __name__ == "__main__":
    run_demo()
