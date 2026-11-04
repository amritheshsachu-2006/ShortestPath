from .dijkstra import run_dijkstra
from .bellman_ford import run_bellman_ford
from .floyd_warshall import run_floyd_warshall
from .bfs import run_bfs
from .dfs import run_dfs

ALGORITHMS = {
    "dijkstra": {
        "name": "Dijkstra's Algorithm",
        "key": "dijkstra",
        "func": run_dijkstra,
        "time_complexity": "O((V + E) log V)",
        "space_complexity": "O(V)",
        "supports_negative": False,
        "guarantees_shortest": True,
        "type": "Single-Source Shortest Path (Priority Queue / Non-negative)"
    },
    "bellman_ford": {
        "name": "Bellman-Ford Algorithm",
        "key": "bellman_ford",
        "func": run_bellman_ford,
        "time_complexity": "O(V · E)",
        "space_complexity": "O(V)",
        "supports_negative": True,
        "guarantees_shortest": True,
        "type": "Single-Source Shortest Path (Dynamic Programming / Negative Edges)"
    },
    "floyd_warshall": {
        "name": "Floyd-Warshall Algorithm",
        "key": "floyd_warshall",
        "func": run_floyd_warshall,
        "time_complexity": "O(V³)",
        "space_complexity": "O(V²)",
        "supports_negative": True,
        "guarantees_shortest": True,
        "type": "All-Pairs Shortest Path (Matrix Dynamic Programming)"
    },
    "bfs": {
        "name": "Breadth-First Search (BFS)",
        "key": "bfs",
        "func": run_bfs,
        "time_complexity": "O(V + E)",
        "space_complexity": "O(V)",
        "supports_negative": False,
        "guarantees_shortest": "Min-Hops Only (Unweighted)",
        "type": "Level-by-Level Graph Traversal (FIFO Queue)"
    },
    "dfs": {
        "name": "Depth-First Search (DFS)",
        "key": "dfs",
        "func": run_dfs,
        "time_complexity": "O(V + E)",
        "space_complexity": "O(V)",
        "supports_negative": False,
        "guarantees_shortest": False,
        "type": "Depth-First Graph Traversal (Stack / Backtracking)"
    }
}

def run_algorithm(algo_key, vertices, edges, adj, source, destination):
    """Executes the specified algorithm."""
    key = algo_key.lower().replace("-", "_").replace(" ", "_")
    if key not in ALGORITHMS:
        # Fallback partial matching
        for k in ALGORITHMS:
            if k in key or key in k:
                key = k
                break

    if key not in ALGORITHMS:
        return {
            "success": False,
            "error": f"Algorithm '{algo_key}' is not recognized. Available: {list(ALGORITHMS.keys())}"
        }

    return ALGORITHMS[key]["func"](vertices, edges, adj, source, destination)

def compare_all_algorithms(vertices, edges, adj, source, destination):
    """Executes all 5 algorithms on the provided graph and returns side-by-side performance results."""
    results = {}
    for key, info in ALGORITHMS.items():
        res = info["func"](vertices, edges, adj, source, destination)
        results[key] = {
            "name": info["name"],
            "key": key,
            "success": res.get("success", False),
            "error": res.get("error"),
            "time_complexity": info["time_complexity"],
            "space_complexity": info["space_complexity"],
            "execution_time_ms": res.get("execution_time_ms", 0),
            "visited_count": res.get("visited_count", 0),
            "relaxations_count": res.get("relaxations_count", 0),
            "path": res.get("path", []),
            "total_distance": res.get("total_distance"),
            "explanation": res.get("explanation", ""),
            "supports_negative": info["supports_negative"],
            "guarantees_shortest": info["guarantees_shortest"],
            "type": info["type"]
        }
    return results

