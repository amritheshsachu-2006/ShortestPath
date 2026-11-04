from collections import deque
import time

def run_bfs(vertices, edges, adj, source, destination):
    """
    Breadth-First Search (BFS) Algorithm.
    Finds the shortest path in terms of minimum number of edges (hops) on unweighted graphs.
    Treats each edge as unit weight 1.
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    start_time = time.perf_counter()
    steps = []

    # Queue stores: (vertex, level)
    queue = deque([source])
    visited_set = {source}
    visited_order = [source]
    predecessors = {v: None for v in vertices}
    hop_distances = {v: float('inf') for v in vertices}
    hop_distances[source] = 0

    step_num = 1
    checks_count = 0

    def format_dist(d):
        return "∞" if d == float('inf') else d

    # Initial Step
    steps.append({
        "step_number": step_num,
        "action": "init",
        "current_vertex": source,
        "current_edge": None,
        "visited": list(visited_order),
        "unvisited": sorted(list(set(vertices) - visited_set)),
        "distances": {k: format_dist(v) for k, v in hop_distances.items()},
        "predecessors": dict(predecessors),
        "data_structure_state": list(queue),
        "highlight_path": [],
        "explanation": f"Initialize BFS: Add source '{source}' to queue at hop distance 0. Mark '{source}' as visited."
    })

    found = False
    while queue:
        u = queue.popleft()
        step_num += 1

        steps.append({
            "step_number": step_num,
            "action": "dequeue",
            "current_vertex": u,
            "current_edge": None,
            "visited": list(visited_order),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {k: format_dist(v) for k, v in hop_distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": list(queue),
            "highlight_path": [],
            "explanation": f"Dequeued vertex '{u}' (level {hop_distances[u]}). Exploring all outgoing neighbors."
        })

        if u == destination:
            found = True
            step_num += 1
            steps.append({
                "step_number": step_num,
                "action": "destination_reached",
                "current_vertex": u,
                "current_edge": None,
                "visited": list(visited_order),
                "unvisited": sorted(list(set(vertices) - visited_set)),
                "distances": {k: format_dist(v) for k, v in hop_distances.items()},
                "predecessors": dict(predecessors),
                "data_structure_state": list(queue),
                "highlight_path": [],
                "explanation": f"Destination '{destination}' reached with minimum edge hops ({hop_distances[u]} hops)."
            })
            break

        # Explore neighbors
        for neighbor, weight in adj.get(u, []):
            checks_count += 1
            step_num += 1

            if neighbor not in visited_set:
                visited_set.add(neighbor)
                visited_order.append(neighbor)
                predecessors[neighbor] = u
                hop_distances[neighbor] = hop_distances[u] + 1
                queue.append(neighbor)

                steps.append({
                    "step_number": step_num,
                    "action": "enqueue_neighbor",
                    "current_vertex": u,
                    "current_edge": [u, neighbor],
                    "visited": list(visited_order),
                    "unvisited": sorted(list(set(vertices) - visited_set)),
                    "distances": {k: format_dist(v) for k, v in hop_distances.items()},
                    "predecessors": dict(predecessors),
                    "data_structure_state": list(queue),
                    "highlight_path": [[u, neighbor]],
                    "explanation": f"Discovered unvisited neighbor '{neighbor}'. Enqueued into FIFO queue at hop distance {hop_distances[neighbor]}. Predecessor[{neighbor}] = '{u}'."
                })
            else:
                steps.append({
                    "step_number": step_num,
                    "action": "already_visited",
                    "current_vertex": u,
                    "current_edge": [u, neighbor],
                    "visited": list(visited_order),
                    "unvisited": sorted(list(set(vertices) - visited_set)),
                    "distances": {k: format_dist(v) for k, v in hop_distances.items()},
                    "predecessors": dict(predecessors),
                    "data_structure_state": list(queue),
                    "highlight_path": [],
                    "explanation": f"Neighbor '{neighbor}' has already been visited. Skipping edge ({u} → {neighbor})."
                })

    # Path reconstruction
    path = []
    total_hops = None
    if destination in visited_set:
        curr = destination
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()
        total_hops = len(path) - 1

    # Also compute actual sum of edge weights along this path for user comparison
    actual_weighted_cost = 0
    if path and len(path) > 1:
        for idx in range(len(path) - 1):
            s_node, t_node = path[idx], path[idx+1]
            # Find weight in adj
            found_w = 1
            for nbr, w in adj.get(s_node, []):
                if nbr == t_node:
                    found_w = w
                    break
            actual_weighted_cost += found_w

    step_num += 1
    path_edges = [[path[k], path[k+1]] for k in range(len(path) - 1)] if len(path) > 1 else []

    if path:
        steps.append({
            "step_number": step_num,
            "action": "completed",
            "current_vertex": destination,
            "current_edge": None,
            "visited": list(visited_order),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {k: format_dist(v) for k, v in hop_distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": [],
            "highlight_path": path_edges,
            "explanation": f"BFS completed! Discovered minimum-hop path: {' → '.join(path)} ({total_hops} hops, total weighted cost = {actual_weighted_cost})."
        })
        explanation = f"BFS found the minimum-hop path from '{source}' to '{destination}' ({' → '.join(path)}) requiring {total_hops} edge hops (sum of edge weights = {actual_weighted_cost}). Note: BFS guarantees the minimum number of edges, but does NOT optimize arbitrary edge weights."
    else:
        steps.append({
            "step_number": step_num,
            "action": "unreachable",
            "current_vertex": destination,
            "current_edge": None,
            "visited": list(visited_order),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {k: format_dist(v) for k, v in hop_distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": [],
            "highlight_path": [],
            "explanation": f"Destination '{destination}' is unreachable from '{source}'."
        })
        explanation = f"Destination '{destination}' is not reachable from '{source}' in the provided graph."

    exec_time = (time.perf_counter() - start_time) * 1000

    return {
        "success": True,
        "error": None,
        "algorithm": "BFS",
        "source": source,
        "destination": destination,
        "path": path,
        "total_distance": actual_weighted_cost if path else None,
        "total_hops": total_hops,
        "visited_nodes": visited_order,
        "visited_count": len(visited_order),
        "relaxations_count": checks_count,
        "execution_time_ms": round(exec_time, 4),
        "time_complexity": "O(V + E)",
        "space_complexity": "O(V)",
        "explanation": explanation,
        "steps": steps
    }

