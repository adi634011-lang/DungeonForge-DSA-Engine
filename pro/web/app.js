/**
 * Main Web UI Controller & Game Engine for DungeonForge.
 */

const canvas = document.getElementById('dungeonCanvas');
const ctx = canvas.getContext('2d');

const GRID_W = 60;
const GRID_H = 36;
const TILE_SIZE = 15; // 60 * 15 = 900px, 36 * 15 = 540px

// State
let bspRoot = null;
let rooms = [];
let mstEdges = [];
let extraEdges = [];
let grid = []; // 0: Wall, 1: Floor, 2: Corridor
let player = { x: 0, y: 0 };
let exitPos = { x: 0, y: 0 };
let treasures = [];
let monsters = [];
let astarPath = null;

let currentStep = 0; // 1: BSP, 2: Rooms, 3: MST, 4: Corridors, 5: Entities, 6: A*
let isGameMode = false;
let playerGold = 0;
let currentFloor = 1;
let monsterMoveTimer = 0;

// UI Elements
const statusText = document.getElementById('pipeline-status');
const statRooms = document.getElementById('stat-rooms');
const statEdges = document.getElementById('stat-edges');
const statLoops = document.getElementById('stat-loops');
const statPathLen = document.getElementById('stat-path-len');
const statSolvable = document.getElementById('stat-solvable');
const gameGoldElem = document.getElementById('game-gold');
const gameFloorElem = document.getElementById('game-floor');
const gameOverlay = document.getElementById('game-overlay');
const overlayTitle = document.getElementById('overlay-title');
const overlayMsg = document.getElementById('overlay-msg');

function initEmptyGrid() {
  grid = Array.from({ length: GRID_H }, () => new Array(GRID_W).fill(0));
}

// ---------------- Pipeline Steps ---------------- //

function step1_BSP() {
  currentStep = 1;
  statusText.textContent = "Step 1: Partitioning 2D Space using BSP Tree...";
  initEmptyGrid();
  rooms = [];
  mstEdges = [];
  extraEdges = [];
  treasures = [];
  monsters = [];
  astarPath = null;

  bspRoot = new BSPNode(0, 0, GRID_W, GRID_H, 0);
  bspRoot.buildTree(4, 7);

  draw();
  updateStats();
}

function step2_Rooms() {
  if (!bspRoot) step1_BSP();
  currentStep = 2;
  statusText.textContent = "Step 2: Carving rectangular rooms inside leaf partitions...";

  initEmptyGrid();
  rooms = bspRoot.createRooms(4, 1, { id: 0 });

  for (const r of rooms) {
    for (let y = r.y; y < r.y + r.h; y++) {
      for (let x = r.x; x < r.x + r.w; x++) {
        if (y >= 0 && y < GRID_H && x >= 0 && x < GRID_W) {
          grid[y][x] = 1;
        }
      }
    }
  }

  draw();
  updateStats();
}

function step3_KruskalMST() {
  if (rooms.length === 0) step2_Rooms();
  currentStep = 3;
  statusText.textContent = "Step 3: Calculating Kruskal's Minimum Spanning Tree with DSU...";

  // Pairwise edges
  let allEdges = [];
  for (let i = 0; i < rooms.length; i++) {
    for (let j = i + 1; j < rooms.length; j++) {
      const dist = Math.hypot(rooms[i].cx - rooms[j].cx, rooms[i].cy - rooms[j].cy);
      allEdges.push({ u: i, v: j, dist });
    }
  }

  // Sort ascending by distance
  allEdges.sort((a, b) => a.dist - b.dist);

  const dsu = new DSU(rooms.length);
  mstEdges = [];
  extraEdges = [];

  for (const edge of allEdges) {
    if (dsu.union(edge.u, edge.v)) {
      mstEdges.push(edge);
    } else if (Math.random() < 0.15) {
      extraEdges.push(edge);
    }
  }

  draw();
  updateStats();
}

function step4_Corridors() {
  if (mstEdges.length === 0) step3_KruskalMST();
  currentStep = 4;
  statusText.textContent = "Step 4: Carving L-shaped grid corridors between rooms...";

  const corridors = [...mstEdges, ...extraEdges];
  for (const edge of corridors) {
    const r1 = rooms[edge.u];
    const r2 = rooms[edge.v];
    carveCorridor({ x: r1.cx, y: r1.cy }, { x: r2.cx, y: r2.cy });
  }

  draw();
  updateStats();
}

function carveCorridor(p1, p2) {
  let x = p1.x;
  let y = p1.y;

  const hFirst = Math.random() < 0.5;

  if (hFirst) {
    while (x !== p2.x) {
      if (grid[y][x] === 0) grid[y][x] = 2;
      x += (p2.x > x) ? 1 : -1;
    }
    while (y !== p2.y) {
      if (grid[y][x] === 0) grid[y][x] = 2;
      y += (p2.y > y) ? 1 : -1;
    }
  } else {
    while (y !== p2.y) {
      if (grid[y][x] === 0) grid[y][x] = 2;
      y += (p2.y > y) ? 1 : -1;
    }
    while (x !== p2.x) {
      if (grid[y][x] === 0) grid[y][x] = 2;
      x += (p2.x > x) ? 1 : -1;
    }
  }
}

function step5_Entities() {
  if (currentStep < 4) step4_Corridors();
  currentStep = 5;
  statusText.textContent = "Step 5: Placing Player, Exit, Monsters and Treasures...";

  if (rooms.length >= 2) {
    player = { x: rooms[0].cx, y: rooms[0].cy };

    // Farthest room
    let maxDist = -1;
    let farRoom = rooms[1];
    for (let i = 1; i < rooms.length; i++) {
      const d = Math.hypot(rooms[i].cx - player.x, rooms[i].cy - player.y);
      if (d > maxDist) {
        maxDist = d;
        farRoom = rooms[i];
      }
    }
    exitPos = { x: farRoom.cx, y: farRoom.cy };
  } else if (rooms.length === 1) {
    player = { x: rooms[0].cx, y: rooms[0].cy };
    exitPos = { x: rooms[0].x + 1, y: rooms[0].y + 1 };
  }

  treasures = [];
  monsters = [];

  for (let i = 0; i < rooms.length; i++) {
    const r = rooms[i];
    if (r.cx === player.x && r.cy === player.y) continue;
    if (r.cx === exitPos.x && r.cy === exitPos.y) continue;

    if (Math.random() < 0.6) {
      treasures.push({
        x: r.x + 1 + Math.floor(Math.random() * (r.w - 2)),
        y: r.y + 1 + Math.floor(Math.random() * (r.h - 2)),
      });
    }

    if (Math.random() < 0.45) {
      monsters.push({
        x: r.x + 1 + Math.floor(Math.random() * (r.w - 2)),
        y: r.y + 1 + Math.floor(Math.random() * (r.h - 2)),
      });
    }
  }

  draw();
  updateStats();
}

function step6_AStar() {
  if (currentStep < 5) step5_Entities();
  currentStep = 6;
  statusText.textContent = "Step 6: Running A* Search with Manhattan Heuristic...";

  astarPath = astarSearch(grid, GRID_W, GRID_H, player, exitPos);

  draw();
  updateStats();
}

function generateCompleteDungeon() {
  step1_BSP();
  step2_Rooms();
  step3_KruskalMST();
  step4_Corridors();
  step5_Entities();
  step6_AStar();
  statusText.textContent = "Complete Dungeon Generated & Fully Solved via A*!";
}

// ---------------- Stats Telemetry ---------------- //

function updateStats() {
  statRooms.textContent = rooms.length;
  statEdges.textContent = mstEdges.length;
  statLoops.textContent = extraEdges.length;
  statPathLen.textContent = astarPath ? astarPath.length : "N/A";
  statSolvable.textContent = astarPath ? "YES ✅" : (currentStep < 6 ? "PENDING" : "NO ❌");
  statSolvable.className = astarPath ? "stat-val text-success" : "stat-val";
  gameGoldElem.textContent = playerGold;
  gameFloorElem.textContent = currentFloor;
}

// ---------------- Rendering ---------------- //

function draw() {
  ctx.fillStyle = '#0a0e17';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // 1. Draw Grid Tiles
  for (let y = 0; y < GRID_H; y++) {
    for (let x = 0; x < GRID_W; x++) {
      const tile = grid[y][x];
      if (tile === 1) {
        // Floor
        ctx.fillStyle = '#1c2842';
        ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE - 0.5, TILE_SIZE - 0.5);
      } else if (tile === 2) {
        // Corridor
        ctx.fillStyle = '#1e3a5f';
        ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE - 0.5, TILE_SIZE - 0.5);
      }
    }
  }

  // 2. Draw BSP Partition Boundaries (if step 1 or 2)
  if (currentStep >= 1 && bspRoot) {
    drawBSPLeaves(bspRoot);
  }

  // 3. Draw MST Connections (if step 3)
  if (currentStep === 3) {
    drawMSTLines();
  }

  // 4. Draw A* Glowing Path
  if (astarPath && astarPath.length > 0) {
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 3;
    ctx.shadowColor = '#00f0ff';
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.moveTo(astarPath[0].x * TILE_SIZE + TILE_SIZE / 2, astarPath[0].y * TILE_SIZE + TILE_SIZE / 2);
    for (let i = 1; i < astarPath.length; i++) {
      ctx.lineTo(astarPath[i].x * TILE_SIZE + TILE_SIZE / 2, astarPath[i].y * TILE_SIZE + TILE_SIZE / 2);
    }
    ctx.stroke();
    ctx.shadowBlur = 0; // reset glow
  }

  // 5. Draw Entities (if step >= 5)
  if (currentStep >= 5) {
    // Treasures ($)
    ctx.fillStyle = '#fbbf24';
    ctx.font = 'bold 12px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (const t of treasures) {
      ctx.fillText('$', t.x * TILE_SIZE + TILE_SIZE / 2, t.y * TILE_SIZE + TILE_SIZE / 2);
    }

    // Exit (>)
    ctx.fillStyle = '#10b981';
    ctx.fillText('>', exitPos.x * TILE_SIZE + TILE_SIZE / 2, exitPos.y * TILE_SIZE + TILE_SIZE / 2);

    // Monsters (M)
    ctx.fillStyle = '#ef4444';
    for (const m of monsters) {
      ctx.fillText('M', m.x * TILE_SIZE + TILE_SIZE / 2, m.y * TILE_SIZE + TILE_SIZE / 2);
    }

    // Player (@)
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('@', player.x * TILE_SIZE + TILE_SIZE / 2, player.y * TILE_SIZE + TILE_SIZE / 2);
  }
}

function drawBSPLeaves(node) {
  if (node.isLeaf()) {
    ctx.strokeStyle = 'rgba(168, 85, 247, 0.4)';
    ctx.lineWidth = 1;
    ctx.strokeRect(node.x * TILE_SIZE, node.y * TILE_SIZE, node.w * TILE_SIZE, node.h * TILE_SIZE);
  } else {
    if (node.left) drawBSPLeaves(node.left);
    if (node.right) drawBSPLeaves(node.right);
  }
}

function drawMSTLines() {
  // MST Spanning Edges (Green)
  ctx.strokeStyle = '#10b981';
  ctx.lineWidth = 2;
  for (const e of mstEdges) {
    const r1 = rooms[e.u];
    const r2 = rooms[e.v];
    ctx.beginPath();
    ctx.moveTo(r1.cx * TILE_SIZE + TILE_SIZE / 2, r1.cy * TILE_SIZE + TILE_SIZE / 2);
    ctx.lineTo(r2.cx * TILE_SIZE + TILE_SIZE / 2, r2.cy * TILE_SIZE + TILE_SIZE / 2);
    ctx.stroke();
  }

  // Extra Loop Edges (Amber dashed)
  ctx.strokeStyle = 'rgba(245, 158, 11, 0.7)';
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 4]);
  for (const e of extraEdges) {
    const r1 = rooms[e.u];
    const r2 = rooms[e.v];
    ctx.beginPath();
    ctx.moveTo(r1.cx * TILE_SIZE + TILE_SIZE / 2, r1.cy * TILE_SIZE + TILE_SIZE / 2);
    ctx.lineTo(r2.cx * TILE_SIZE + TILE_SIZE / 2, r2.cy * TILE_SIZE + TILE_SIZE / 2);
    ctx.stroke();
  }
  ctx.setLineDash([]); // Reset
}

// ---------------- Game Movement & AI ---------------- //

function handleKeyDown(e) {
  if (!isGameMode) return;

  let dx = 0;
  let dy = 0;

  if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') dy = -1;
  else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') dy = 1;
  else if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') dx = -1;
  else if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') dx = 1;
  else return;

  e.preventDefault();

  const nx = player.x + dx;
  const ny = player.y + dy;

  // Collision with wall
  if (nx < 0 || nx >= GRID_W || ny < 0 || ny >= GRID_H || grid[ny][nx] === 0) {
    return;
  }

  player.x = nx;
  player.y = ny;

  // Check Treasure Pickup
  const tIdx = treasures.findIndex(t => t.x === player.x && t.y === player.y);
  if (tIdx !== -1) {
    treasures.splice(tIdx, 1);
    playerGold += 10;
    statusText.textContent = `Collected 10 Gold! Total: ${playerGold} 🪙`;
    updateStats();
  }

  // Check Exit
  if (player.x === exitPos.x && player.y === exitPos.y) {
    overlayTitle.textContent = `Floor ${currentFloor} Cleared! 🏆`;
    overlayMsg.textContent = `Great navigation! You collected ${playerGold} Gold so far.`;
    gameOverlay.classList.remove('hidden');
    return;
  }

  // Update Monsters using A* toward player
  updateMonsters();

  // Recompute A* path from new player position to exit
  astarPath = astarSearch(grid, GRID_W, GRID_H, player, exitPos);

  draw();
}

function updateMonsters() {
  for (const m of monsters) {
    // Only chase if within distance of 14 tiles
    const dist = Math.hypot(m.x - player.x, m.y - player.y);
    if (dist <= 14) {
      const path = astarSearch(grid, GRID_W, GRID_H, m, player);
      if (path && path.length > 1) {
        m.x = path[1].x;
        m.y = path[1].y;
      }
    }

    // Check monster caught player
    if (m.x === player.x && m.y === player.y) {
      overlayTitle.textContent = "Defeated by Monster! 💀";
      overlayMsg.textContent = "A monster intercepted your path. Try again!";
      gameOverlay.classList.remove('hidden');
    }
  }
}

// ---------------- Event Listeners ---------------- //

document.getElementById('btn-auto-gen').addEventListener('click', generateCompleteDungeon);
document.getElementById('btn-step-bsp').addEventListener('click', step1_BSP);
document.getElementById('btn-step-rooms').addEventListener('click', step2_Rooms);
document.getElementById('btn-step-mst').addEventListener('click', step3_KruskalMST);
document.getElementById('btn-step-corridors').addEventListener('click', step4_Corridors);
document.getElementById('btn-step-entities').addEventListener('click', step5_Entities);
document.getElementById('btn-step-astar').addEventListener('click', step6_AStar);

const btnViz = document.getElementById('btn-mode-viz');
const btnPlay = document.getElementById('btn-mode-play');

btnViz.addEventListener('click', () => {
  isGameMode = false;
  btnViz.classList.add('active');
  btnPlay.classList.remove('active');
  statusText.textContent = "Algorithm Visualizer Mode: Click steps or Auto-Generate.";
});

btnPlay.addEventListener('click', () => {
  isGameMode = true;
  btnPlay.classList.add('active');
  btnViz.classList.remove('active');
  statusText.textContent = "Game Mode Active! Move with WASD/Arrows to reach (>) and grab ($)!";
  if (currentStep < 6) generateCompleteDungeon();
});

document.getElementById('btn-next-floor').addEventListener('click', () => {
  gameOverlay.classList.add('hidden');
  currentFloor++;
  generateCompleteDungeon();
  isGameMode = true;
  btnPlay.classList.add('active');
  btnViz.classList.remove('active');
});

window.addEventListener('keydown', handleKeyDown);

// Auto-run on load
generateCompleteDungeon();
