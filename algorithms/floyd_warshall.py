import time
import math

def run_floyd_warshall(vertices, edges, adj, source, destination):
    """
    Floyd-Warshall All-Pairs Shortest Path Algorithm.
    Computes all-pairs shortest paths and detects negative cycles on the diagonal.
    Reconstructs shortest path between specific source and destination.
    Time Complexity: O(V^3)
    Space Complexity: O(V^2)
    """
    start_time = time.perf_counter()
    steps = []
    
    v_list = sorted(list(vertices))
    n = len(v_list)

    def format_val(val):
        if val == float('inf'):
            return "∞"
        if isinstance(val, float) and val.is_integer():
            return int(val)
        return round(val, 2) if isinstance(val, float) else val

    # 1. Initialize distance matrix and next_node reconstruction matrix
    dist = {u: {v: float('inf') for v in v_list} for u in v_list}
    next_node = {u: {v: None for v in v_list} for u in v_list}

    for v in v_list:
        dist[v][v] = 0
        next_node[v][v] = v

    for u, v, weight, directed in edges:
        # If multiple edges exist between u and v, take the minimum
        if weight < dist[u][v]:
            dist[u][v] = weight
            next_node[u][v] = v
        if not directed:
            if weight < dist[v][u]:
                dist[v][u] = weight
                next_node[v][u] = u

    relaxations_count = 0
    step_num = 1

    def snapshot_matrix():
        return {u: {v: format_val(dist[u][v]) for v in v_list} for u in v_list}

    steps.append({
        "step_number": step_num,
        "iteration": "Initialization",
        "action": "init_matrix",
        "current_vertex": source,
        "pivot_vertex": None,
        "current_edge": None,
        "visited": [],
        "unvisited": v_list,
        "distances": {v: format_val(dist[source][v]) for v in v_list},
        "matrix": snapshot_matrix(),
        "predecessors": {},
        "data_structure_state": {"pivot": None, "matrix": snapshot_matrix()},
        "highlight_path": [],
        "explanation": f"Initialized distance matrix D(0) and next-hop matrix for all {n} vertices. Diagonal values are 0; direct edges filled with initial weights."
    })

    # Triple loop: k is the intermediate pivot vertex
    for k_idx, k in enumerate(v_list):
        pivot_updates = 0
        for i in v_list:
            for j in v_list:
                if dist[i][k] != float('inf') and dist[k][j] != float('inf'):
                    new_dist = dist[i][k] + dist[k][j]
                    if new_dist < dist[i][j]:
                        old_dist = dist[i][j]
                        dist[i][j] = new_dist
                        next_node[i][j] = next_node[i][k]
                        relaxations_count += 1
                        pivot_updates += 1

        # Record a step per intermediate pivot k
        step_num += 1
        steps.append({
            "step_number": step_num,
            "iteration": f"Pivot {k} ({k_idx + 1} of {n})",
            "action": "pivot_processed",
            "current_vertex": k,
            "pivot_vertex": k,
            "current_edge": None,
            "visited": v_list[:k_idx + 1],
            "unvisited": v_list[k_idx + 1:],
            "distances": {v: format_val(dist[source][v]) for v in v_list},
            "matrix": snapshot_matrix(),
            "predecessors": {},
            "data_structure_state": {"pivot": k, "updates_in_pass": pivot_updates, "matrix": snapshot_matrix()},
            "highlight_path": [],
            "explanation": f"Evaluated paths using intermediate pivot '{k}'. Found {pivot_updates} shorter paths passing through '{k}'."
        })

    # Check for negative-weight cycle (negative values on the main diagonal)
    negative_cycle = False
    for v in v_list:
        if dist[v][v] < 0:
            negative_cycle = True
            break

    exec_time = (time.perf_counter() - start_time) * 1000

    if negative_cycle:
        step_num += 1
        steps.append({
            "step_number": step_num,
            "iteration": "Negative Cycle Check",
            "action": "negative_cycle",
            "current_vertex": None,
            "pivot_vertex": None,
            "current_edge": None,
            "visited": v_list,
            "unvisited": [],
            "distances": {v: format_val(dist[source][v]) for v in v_list},
            "matrix": snapshot_matrix(),
            "predecessors": {},
            "data_structure_state": {"negative_cycle": True},
            "highlight_path": [],
            "explanation": f"NEGATIVE-WEIGHT CYCLE DETECTED! Negative diagonal entry found: dist[{v}][{v}] = {dist[v][v]} < 0."
        })
        return {
            "success": False,
            "error": "Negative-weight cycle detected in the graph. At least one diagonal element is negative, meaning a cycle with negative total cost exists.",
            "algorithm": "Floyd-Warshall",
            "source": source,
            "destination": destination,
            "path": [],
            "total_distance": None,
            "visited_nodes": v_list,
            "visited_count": n,
            "relaxations_count": relaxations_count,
            "execution_time_ms": round(exec_time, 4),
            "time_complexity": "O(V³)",
            "space_complexity": "O(V²)",
            "explanation": "Floyd-Warshall detected a negative cycle. When dist[i][i] < 0, vertex i can cycle back to itself with negative cost.",
            "matrix": snapshot_matrix(),
            "steps": steps
        }

    # Shortest path reconstruction from source to destination
    path = []
    total_dist = None

    if dist[source][destination] != float('inf'):
        curr = source
        visited_in_path = {curr}
        path.append(curr)
        while curr != destination:
            curr = next_node[curr][destination]
            if curr is None or curr in visited_in_path:
                # Cycle or broken path detected
                break
            visited_in_path.add(curr)
            path.append(curr)

        if path and path[-1] == destination:
            total_dist = dist[source][destination]
            if isinstance(total_dist, float) and total_dist.is_integer():
                total_dist = int(total_dist)
        else:
            path = []

    step_num += 1
    path_edges = [[path[k], path[k+1]] for k in range(len(path) - 1)] if len(path) > 1 else []

    if path:
        steps.append({
            "step_number": step_num,
            "iteration": "Final Result",
            "action": "completed",
            "current_vertex": destination,
            "pivot_vertex": None,
            "current_edge": None,
            "visited": v_list,
            "unvisited": [],
            "distances": {v: format_val(dist[source][v]) for v in v_list},
            "matrix": snapshot_matrix(),
            "predecessors": {},
            "data_structure_state": {"completed": True},
            "highlight_path": path_edges,
            "explanation": f"Floyd-Warshall completed all-pairs analysis. Reconstructed path from '{source}' to '{destination}': {' → '.join(path)} with total distance {total_dist}."
        })
        explanation = f"Floyd-Warshall calculated all-pairs shortest paths in O(V³). Shortest path from '{source}' to '{destination}': {' → '.join(path)} with cost {total_dist}. Performed {relaxations_count} matrix cell relaxations."
    else:
        steps.append({
            "step_number": step_num,
            "iteration": "Final Result",
            "action": "unreachable",
            "current_vertex": destination,
            "pivot_vertex": None,
            "current_edge": None,
            "visited": v_list,
            "unvisited": [],
            "distances": {v: format_val(dist[source][v]) for v in v_list},
            "matrix": snapshot_matrix(),
            "predecessors": {},
            "data_structure_state": {"completed": True},
            "highlight_path": [],
            "explanation": f"Destination '{destination}' is unreachable from '{source}'."
        })
        explanation = f"Destination '{destination}' is not reachable from '{source}' in the all-pairs distance matrix."

    return {
        "success": True,
        "error": None,
        "algorithm": "Floyd-Warshall",
        "source": source,
        "destination": destination,
        "path": path,
        "total_distance": total_dist,
        "visited_nodes": v_list,
        "visited_count": n,
        "relaxations_count": relaxations_count,
        "execution_time_ms": round(exec_time, 4),
        "time_complexity": "O(V³)",
        "space_complexity": "O(V²)",
        "explanation": explanation,
        "matrix": snapshot_matrix(),
        "steps": steps
    }

