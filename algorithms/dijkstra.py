import heapq
import time
import math

def run_dijkstra(vertices, edges, adj, source, destination):
    """
    Dijkstra's Shortest Path Algorithm using a binary heap priority queue.
    Strictly non-negative edge weights only.
    Time Complexity: O((V + E) log V)
    Space Complexity: O(V)
    """
    start_time = time.perf_counter()
    steps = []
    
    # 1. Validation: check for negative weights
    for u, v, weight, _ in edges:
        if weight < 0:
            exec_time = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "error": f"Negative edge weight detected ({u} -> {v} with weight {weight}). Dijkstra's algorithm requires strictly non-negative edge weights. Please use the Bellman-Ford algorithm instead.",
                "algorithm": "Dijkstra",
                "source": source,
                "destination": destination,
                "path": [],
                "total_distance": None,
                "visited_nodes": [],
                "visited_count": 0,
                "relaxations_count": 0,
                "execution_time_ms": round(exec_time, 4),
                "time_complexity": "O((V + E) log V)",
                "space_complexity": "O(V)",
                "explanation": "Dijkstra's algorithm cannot handle negative edge weights because its greedy strategy assumes that adding edges can only increase path cost.",
                "steps": []
            }

    # 2. Initialization
    distances = {v: float('inf') for v in vertices}
    predecessors = {v: None for v in vertices}
    distances[source] = 0
    
    visited_set = set()
    visited_order = []
    relaxations_count = 0
    step_num = 1

    # Priority queue stores tuples: (distance, vertex_id)
    pq = [(0, source)]

    def format_dist(d):
        return "∞" if math.isinf(d) else (int(d) if isinstance(d, float) and d.is_integer() else round(d, 2))

    # Initial Step
    steps.append({
        "step_number": step_num,
        "action": "init",
        "current_vertex": source,
        "current_edge": None,
        "visited": list(visited_set),
        "unvisited": sorted(list(set(vertices) - visited_set)),
        "distances": {k: format_dist(v) for k, v in distances.items()},
        "predecessors": dict(predecessors),
        "data_structure_state": [{"vertex": v, "distance": d} for d, v in sorted(pq)],
        "highlight_path": [],
        "explanation": f"Initialize distances: dist[{source}] = 0, all other vertices set to ∞. Add source {source} to priority queue."
    })

    while pq:
        current_dist, u = heapq.heappop(pq)

        if u in visited_set:
            continue

        visited_set.add(u)
        visited_order.append(u)
        step_num += 1

        steps.append({
            "step_number": step_num,
            "action": "select_vertex",
            "current_vertex": u,
            "current_edge": None,
            "visited": list(visited_order),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {k: format_dist(v) for k, v in distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": [{"vertex": v, "distance": d} for d, v in sorted(pq)],
            "highlight_path": [],
            "explanation": f"Selected vertex '{u}' with minimum tentative distance {format_dist(current_dist)} from priority queue. Marked as visited."
        })

        if u == destination:
            step_num += 1
            steps.append({
                "step_number": step_num,
                "action": "destination_reached",
                "current_vertex": u,
                "current_edge": None,
                "visited": list(visited_order),
                "unvisited": sorted(list(set(vertices) - visited_set)),
                "distances": {k: format_dist(v) for k, v in distances.items()},
                "predecessors": dict(predecessors),
                "data_structure_state": [{"vertex": v, "distance": d} for d, v in sorted(pq)],
                "highlight_path": [],
                "explanation": f"Destination '{destination}' reached! Optimal shortest path is guaranteed."
            })
            break

        # Relax outgoing edges
        for neighbor, weight in adj.get(u, []):
            if neighbor in visited_set:
                continue

            new_dist = current_dist + weight
            step_num += 1

            if new_dist < distances[neighbor]:
                old_dist = distances[neighbor]
                distances[neighbor] = new_dist
                predecessors[neighbor] = u
                heapq.heappush(pq, (new_dist, neighbor))
                relaxations_count += 1

                steps.append({
                    "step_number": step_num,
                    "action": "relax_edge",
                    "current_vertex": u,
                    "current_edge": [u, neighbor],
                    "visited": list(visited_order),
                    "unvisited": sorted(list(set(vertices) - visited_set)),
                    "distances": {k: format_dist(v) for k, v in distances.items()},
                    "predecessors": dict(predecessors),
                    "data_structure_state": [{"vertex": v, "distance": d} for d, v in sorted(pq)],
                    "highlight_path": [[u, neighbor]],
                    "explanation": f"Edge ({u} → {neighbor}, wt={weight}) relaxed! Shorter path found: {format_dist(old_dist)} → {format_dist(new_dist)}. Updated predecessor[{neighbor}] = '{u}'."
                })
            else:
                steps.append({
                    "step_number": step_num,
                    "action": "skip_edge",
                    "current_vertex": u,
                    "current_edge": [u, neighbor],
                    "visited": list(visited_order),
                    "unvisited": sorted(list(set(vertices) - visited_set)),
                    "distances": {k: format_dist(v) for k, v in distances.items()},
                    "predecessors": dict(predecessors),
                    "data_structure_state": [{"vertex": v, "distance": d} for d, v in sorted(pq)],
                    "highlight_path": [],
                    "explanation": f"Edge ({u} → {neighbor}, wt={weight}) evaluated: new distance {format_dist(new_dist)} ≥ current distance {format_dist(distances[neighbor])}. No relaxation needed."
                })

    # Path reconstruction
    path = []
    total_dist = None
    if distances[destination] != float('inf'):
        curr = destination
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()
        total_dist = distances[destination]
        if isinstance(total_dist, float) and total_dist.is_integer():
            total_dist = int(total_dist)

    # Final step
    step_num += 1
    path_edges = [[path[i], path[i+1]] for i in range(len(path) - 1)] if len(path) > 1 else []
    
    if path:
        steps.append({
            "step_number": step_num,
            "action": "completed",
            "current_vertex": destination,
            "current_edge": None,
            "visited": list(visited_order),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {k: format_dist(v) for k, v in distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": [],
            "highlight_path": path_edges,
            "explanation": f"Algorithm completed successfully. Shortest path from '{source}' to '{destination}': {' → '.join(path)} with total cost {total_dist}."
        })
        explanation = f"Dijkstra found the optimal path from '{source}' to '{destination}' ({' → '.join(path)}) with total cost {total_dist}. Explored {len(visited_order)} vertices and performed {relaxations_count} edge relaxations."
    else:
        steps.append({
            "step_number": step_num,
            "action": "unreachable",
            "current_vertex": destination,
            "current_edge": None,
            "visited": list(visited_order),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {k: format_dist(v) for k, v in distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": [],
            "highlight_path": [],
            "explanation": f"Destination '{destination}' is unreachable from source '{source}'."
        })
        explanation = f"Destination '{destination}' is not reachable from '{source}' in the provided graph."

    exec_time = (time.perf_counter() - start_time) * 1000

    return {
        "success": True,
        "error": None,
        "algorithm": "Dijkstra",
        "source": source,
        "destination": destination,
        "path": path,
        "total_distance": total_dist,
        "visited_nodes": visited_order,
        "visited_count": len(visited_order),
        "relaxations_count": relaxations_count,
        "execution_time_ms": round(exec_time, 4),
        "time_complexity": "O((V + E) log V)",
        "space_complexity": "O(V)",
        "explanation": explanation,
        "steps": steps
    }

