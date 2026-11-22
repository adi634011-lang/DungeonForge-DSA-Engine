/**
 * DSA Engine in JavaScript for Web Visualizer:
 * 1. Disjoint Set Union (Union-Find) with Path Compression & Rank
 * 2. Binary Space Partitioning (BSP Tree)
 * 3. Kruskal's Minimum Spanning Tree
 * 4. Priority Queue (Min-Heap)
 * 5. A* Search Shortest Pathfinding
 */

class DSU {
  constructor(size) {
    this.parent = Array.from({ length: size }, (_, i) => i);
    this.rank = new Array(size).fill(0);
    this.numSets = size;
  }

  find(i) {
    if (this.parent[i] !== i) {
      this.parent[i] = this.find(this.parent[i]); // Path compression
    }
    return this.parent[i];
  }

  union(i, j) {
    const rootI = this.find(i);
    const rootJ = this.find(j);

    if (rootI === rootJ) return false; // Cycle detected

    // Union by rank
    if (this.rank[rootI] < this.rank[rootJ]) {
      this.parent[rootI] = rootJ;
    } else if (this.rank[rootI] > this.rank[rootJ]) {
      this.parent[rootJ] = rootI;
    } else {
      this.parent[rootJ] = rootI;
      this.rank[rootI]++;
    }

    this.numSets--;
    return true;
  }
}

class BSPNode {
  constructor(x, y, w, h, depth = 0) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
    this.depth = depth;
    this.left = null;
    this.right = null;
    this.room = null;
  }

  isLeaf() {
    return this.left === null && this.right === null;
  }

  split(minSize = 7) {
    if (!this.isLeaf()) return false;
    if (this.w < minSize * 2 && this.h < minSize * 2) return false;

    let splitH;
    if (this.w / Math.max(1, this.h) >= 1.25) {
      splitH = false; // vertical split
    } else if (this.h / Math.max(1, this.w) >= 1.25) {
      splitH = true; // horizontal split
    } else {
      splitH = Math.random() < 0.5;
    }

    const maxSplit = (splitH ? this.h : this.w) - minSize;
    if (maxSplit <= minSize) return false;

    const splitPos = Math.floor(minSize + Math.random() * (maxSplit - minSize));

    if (splitH) {
      this.left = new BSPNode(this.x, this.y, this.w, splitPos, this.depth + 1);
      this.right = new BSPNode(this.x, this.y + splitPos, this.w, this.h - splitPos, this.depth + 1);
    } else {
      this.left = new BSPNode(this.x, this.y, splitPos, this.h, this.depth + 1);
      this.right = new BSPNode(this.x + splitPos, this.y, this.w - splitPos, this.h, this.depth + 1);
    }
    return true;
  }

  buildTree(maxDepth = 4, minSize = 7) {
    if (this.depth >= maxDepth) return;
    if (this.split(minSize)) {
      if (this.left) this.left.buildTree(maxDepth, minSize);
      if (this.right) this.right.buildTree(maxDepth, minSize);
    }
  }

  getLeafNodes() {
    if (this.isLeaf()) return [this];
    let leaves = [];
    if (this.left) leaves.push(...this.left.getLeafNodes());
    if (this.right) leaves.push(...this.right.getLeafNodes());
    return leaves;
  }

  createRooms(minRoomSize = 4, padding = 1, counter = { id: 0 }) {
    let rooms = [];
    if (this.isLeaf()) {
      const maxW = this.w - 2 * padding;
      const maxH = this.h - 2 * padding;
      if (maxW >= minRoomSize && maxH >= minRoomSize) {
        const rw = Math.floor(minRoomSize + Math.random() * (maxW - minRoomSize + 1));
        const rh = Math.floor(minRoomSize + Math.random() * (maxH - minRoomSize + 1));
        const rx = this.x + padding + Math.floor(Math.random() * (maxW - rw + 1));
        const ry = this.y + padding + Math.floor(Math.random() * (maxH - rh + 1));

        this.room = {
          id: counter.id++,
          x: rx,
          y: ry,
          w: rw,
          h: rh,
          cx: Math.floor(rx + rw / 2),
          cy: Math.floor(ry + rh / 2),
        };
        rooms.push(this.room);
      }
    } else {
      if (this.left) rooms.push(...this.left.createRooms(minRoomSize, padding, counter));
      if (this.right) rooms.push(...this.right.createRooms(minRoomSize, padding, counter));
    }
    return rooms;
  }
}

class MinHeap {
  constructor() {
    this.heap = [];
  }

  push(item) {
    this.heap.push(item);
    this._bubbleUp(this.heap.length - 1);
  }

  pop() {
    if (this.heap.length === 0) return null;
    const top = this.heap[0];
    const bottom = this.heap.pop();
    if (this.heap.length > 0) {
      this.heap[0] = bottom;
      this._sinkDown(0);
    }
    return top;
  }

  isEmpty() {
    return this.heap.length === 0;
  }

  _bubbleUp(idx) {
    while (idx > 0) {
      const parentIdx = Math.floor((idx - 1) / 2);
      if (this.heap[idx].f < this.heap[parentIdx].f) {
        [this.heap[idx], this.heap[parentIdx]] = [this.heap[parentIdx], this.heap[idx]];
        idx = parentIdx;
      } else {
        break;
      }
    }
  }

  _sinkDown(idx) {
    const len = this.heap.length;
    while (true) {
      let smallest = idx;
      const left = 2 * idx + 1;
      const right = 2 * idx + 2;

      if (left < len && this.heap[left].f < this.heap[smallest].f) smallest = left;
      if (right < len && this.heap[right].f < this.heap[smallest].f) smallest = right;

      if (smallest !== idx) {
        [this.heap[idx], this.heap[smallest]] = [this.heap[smallest], this.heap[idx]];
        idx = smallest;
      } else {
        break;
      }
    }
  }
}

function astarSearch(grid, width, height, start, goal) {
  const key = (x, y) => `${x},${y}`;
  const unkey = (k) => k.split(',').map(Number);

  const manhattan = (p1, p2) => Math.abs(p1.x - p2.x) + Math.abs(p1.y - p2.y);

  const openHeap = new MinHeap();
  openHeap.push({ x: start.x, y: start.y, f: manhattan(start, goal) });

  const cameFrom = new Map();
  const gScore = new Map();
  const closedSet = new Set();

  gScore.set(key(start.x, start.y), 0);

  const dirs = [
    { dx: 0, dy: 1 },
    { dx: 0, dy: -1 },
    { dx: 1, dy: 0 },
    { dx: -1, dy: 0 },
  ];

  while (!openHeap.isEmpty()) {
    const current = openHeap.pop();
    const currKey = key(current.x, current.y);

    if (current.x === goal.x && current.y === goal.y) {
      // Reconstruct path
      let path = [{ x: current.x, y: current.y }];
      let traceKey = currKey;
      while (cameFrom.has(traceKey)) {
        traceKey = cameFrom.get(traceKey);
        const [tx, ty] = unkey(traceKey);
        path.push({ x: tx, y: ty });
      }
      path.reverse();
      return path;
    }

    closedSet.add(currKey);

    for (const d of dirs) {
      const nx = current.x + d.dx;
      const ny = current.y + d.dy;
      const nKey = key(nx, ny);

      if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
      if (grid[ny][nx] === 0) continue; // Wall tile
      if (closedSet.has(nKey)) continue;

      const tentativeG = (gScore.get(currKey) ?? Infinity) + 1;

      if (tentativeG < (gScore.get(nKey) ?? Infinity)) {
        cameFrom.set(nKey, currKey);
        gScore.set(nKey, tentativeG);
        const f = tentativeG + manhattan({ x: nx, y: ny }, goal);
        openHeap.push({ x: nx, y: ny, f });
      }
    }
  }

  return null;
}
