"""
Polaris AI - 8-Directional A* Graph Search Engine
Computes optimal maritime navigation trajectory through fused dynamic risk matrix.
Enforces hard safety constraint: Risk >= 95 is treated as strictly impassable.
"""

import heapq
import numpy as np
from typing import List, Tuple, Optional, Dict

import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from constants import GRID_SIZE, index_to_latlon


def run_a_star(
    risk_matrix: np.ndarray,
    start_idx: Tuple[int, int],
    goal_idx: Tuple[int, int]
) -> Optional[List[Tuple[float, float]]]:
    """
    Executes 8-directional A* pathfinding over the 50x50 risk grid.
    Returns:
        List of [lat, lon] waypoints on success, or None if goal is unreachable.
    """
    rows, cols = risk_matrix.shape

    # Start or goal in impassable hazard is immediately unreachable
    if risk_matrix[start_idx[0], start_idx[1]] >= 95.0 or risk_matrix[goal_idx[0], goal_idx[1]] >= 95.0:
        return None

    def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        # Euclidean distance heuristic
        return float(np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2))

    # 8-directional neighbor offsets (cardinal + diagonal)
    neighbors_offsets = [
        (-1, 0, 1.0),    # North (cardinal)
        (1, 0, 1.0),     # South (cardinal)
        (0, -1, 1.0),    # West (cardinal)
        (0, 1, 1.0),     # East (cardinal)
        (-1, -1, 1.414), # North-West (diagonal)
        (-1, 1, 1.414),  # North-East (diagonal)
        (1, -1, 1.414),  # South-West (diagonal)
        (1, 1, 1.414)    # South-East (diagonal)
    ]

    open_set: List[Tuple[float, Tuple[int, int]]] = []
    heapq.heappush(open_set, (0.0, start_idx))

    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score: Dict[Tuple[int, int], float] = {start_idx: 0.0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal_idx:
            # Reconstruct path from goal back to start
            path_indices: List[Tuple[int, int]] = []
            curr_node = current
            while curr_node in came_from:
                path_indices.append(curr_node)
                curr_node = came_from[curr_node]
            path_indices.append(start_idx)
            path_indices.reverse()

            # Map grid indices (r, c) back to real GPS (lat, lon) coordinates
            waypoints: List[Tuple[float, float]] = [
                index_to_latlon(r, c) for r, c in path_indices
            ]
            return waypoints

        for dr, dc, dist in neighbors_offsets:
            nr, nc = current[0] + dr, current[1] + dc

            # Bounds check
            if 0 <= nr < rows and 0 <= nc < cols:
                cell_risk = float(risk_matrix[nr, nc])

                # EXACT LINE FOR CITATION: Hard safety constraint enforcement
                # Line identifier: HARD_SAFETY_RISK_95_SKIP
                if cell_risk >= 95.0:
                    # Treat cell as impassable (cost = infinity); early skip in neighbor expansion
                    continue

                # Edge cost formula: Δdistance + 0.45 * Risk Score
                edge_cost = dist + (0.45 * cell_risk)
                tentative_g = g_score[current] + edge_cost

                if (nr, nc) not in g_score or tentative_g < g_score[(nr, nc)]:
                    came_from[(nr, nc)] = current
                    g_score[(nr, nc)] = tentative_g
                    f_score = tentative_g + heuristic((nr, nc), goal_idx)
                    heapq.heappush(open_set, (f_score, (nr, nc)))

    # No viable route without crossing Risk >= 95
    return None
