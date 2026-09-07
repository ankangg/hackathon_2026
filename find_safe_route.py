import numpy as np
import heapq
import matplotlib.pyplot as plt
import os

# ============================================================
# INITIALIZATION
# ============================================================
GRID_FILE = r"data\risk_grid.npy"
OUTPUT_DIR = r"output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("A* ROUTE PLANNING: CALCULATING SAFE NAVIGATION PATH")
print("=" * 70)

# Load risk grid
risk_grid = np.load(GRID_FILE)
GRID_SIZE = risk_grid.shape[0]

# Define start (top-left) and destination (bottom-right)
START = (0, 0)
GOAL = (GRID_SIZE - 1, GRID_SIZE - 1)

# ============================================================
# A* ALGORITHM
# ============================================================
def heuristic(a, b):
    # Euclidean distance
    return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def get_neighbors(node):
    neighbors = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0: continue
            x, y = node[0] + dx, node[1] + dy
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                neighbors.append((x, y))
    return neighbors

print(f"Planning route from {START} to {GOAL}...")

# Priority queue: (f_score, node)
open_set = []
heapq.heappush(open_set, (0, START))

came_from = {}
g_score = {START: 0}

while open_set:
    _, current = heapq.heappop(open_set)

    if current == GOAL:
        break

    for neighbor in get_neighbors(current):
        # Movement cost: 1 for straight, 1.414 for diagonal
        dist = 1 if current[0] == neighbor[0] or current[1] == neighbor[1] else 1.414
        
        # Risk penalty: heavy penalty for high risk cells
        risk = risk_grid[neighbor[0], neighbor[1]]
        
        # Absolute blocker: Avoid 100-risk completely (icebergs)
        if risk == 100:
            continue
            
        tentative_g_score = g_score[current] + dist + (risk * 0.5)

        if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
            came_from[neighbor] = current
            g_score[neighbor] = tentative_g_score
            f_score = tentative_g_score + heuristic(neighbor, GOAL)
            heapq.heappush(open_set, (f_score, neighbor))

# Reconstruct path
path = []
current = GOAL
while current in came_from:
    path.append(current)
    current = came_from[current]
path.append(START)
path.reverse()

print(f"Path found! Total route length: {len(path)} waypoints.")

# ============================================================
# VISUALIZATION
# ============================================================
print("Generating route visualization...")
plt.figure(figsize=(10, 8))

# Draw the risk environment
plt.imshow(risk_grid, cmap='inferno', origin='upper')
plt.colorbar(label='Navigational Risk (0-100)')

# Draw the calculated path
path_y, path_x = zip(*path)
plt.plot(path_x, path_y, color='cyan', linewidth=2.5, label='Safe Route (A*)', marker='.', markersize=4)

# Mark Start and Goal
plt.scatter([START[1]], [START[0]], color='lime', s=100, label='Start', zorder=5)
plt.scatter([GOAL[1]], [GOAL[0]], color='red', s=100, label='Destination', zorder=5)

plt.title("SAFE NAVIGATION ROUTE: Sea Ice & Weather Avoidance")
plt.legend()

# Save image
out_file = os.path.join(OUTPUT_DIR, "safe_route_map.png")
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"Saved route map to: {out_file}")

print("\n" + "=" * 70)
print("PIPELINE COMPLETE: ALL MODULES EXECUTED SUCCESSFULLY")
print("=" * 70)

# Display the map on screen
plt.show()