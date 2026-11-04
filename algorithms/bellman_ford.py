import time
import math

def run_bellman_ford(vertices, edges, adj, source, destination):
    """
    Bellman-Ford Shortest Path Algorithm.
    Supports negative edge weights and detects negative-weight cycles.
    Time Complexity: O(V * E)
    Space Complexity: O(V)
    """
    start_time = time.perf_counter()
    steps = []
    
    # Initialization
    distances = {v: float('inf') for v in vertices}
    predecessors = {v: None for v in vertices}
    distances[source] = 0

    visited_set = {source}
    relaxations_count = 0
    step_num = 1
    num_vertices = len(vertices)

    def format_dist(d):
        return "∞" if math.isinf(d) else (int(d) if isinstance(d, float) and d.is_integer() else round(d, 2))

    # Flatten edges list: (u, v, weight)
    flat_edges = []
    for u, v, weight, directed in edges:
        flat_edges.append((u, v, weight))
        if not directed:
            flat_edges.append((v, u, weight))

    # Deduplicate edges if any
    unique_edges = []
    seen_edges = set()
    for u, v, w in flat_edges:
        if (u, v, w) not in seen_edges:
            seen_edges.add((u, v, w))
            unique_edges.append((u, v, w))

    steps.append({
        "step_number": step_num,
        "iteration": "Initialization",
        "action": "init",
        "current_vertex": source,
        "current_edge": None,
        "visited": list(visited_set),
        "unvisited": sorted(list(set(vertices) - visited_set)),
        "distances": {k: format_dist(v) for k, v in distances.items()},
        "predecessors": dict(predecessors),
        "data_structure_state": {"iteration": 0, "max_iterations": num_vertices - 1},
        "highlight_path": [],
        "explanation": f"Initialize distances: dist[{source}] = 0, all others = ∞. Will perform at most {num_vertices - 1} relaxation passes over all {len(unique_edges)} edges."
    })

    # Relaxation passes (V - 1 times)
    negative_cycle_detected = False
    cycle_nodes = []

    for i in range(1, num_vertices):
        updated_in_this_pass = False
        step_num += 1
        steps.append({
            "step_number": step_num,
            "iteration": f"Pass {i} of {num_vertices - 1}",
            "action": "pass_start",
            "current_vertex": None,
            "current_edge": None,
            "visited": list(visited_set),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {k: format_dist(v) for k, v in distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": {"iteration": i, "max_iterations": num_vertices - 1},
            "highlight_path": [],
            "explanation": f"Starting relaxation pass {i} of {num_vertices - 1}. Checking all edges."
        })

        for u, v, weight in unique_edges:
            if distances[u] != float('inf'):
                new_dist = distances[u] + weight
                if new_dist < distances[v]:
                    old_dist = distances[v]
                    distances[v] = new_dist
                    predecessors[v] = u
                    visited_set.add(u)
                    visited_set.add(v)
                    relaxations_count += 1
                    updated_in_this_pass = True

                    step_num += 1
                    steps.append({
                        "step_number": step_num,
                        "iteration": f"Pass {i} of {num_vertices - 1}",
                        "action": "relax_edge",
                        "current_vertex": u,
                        "current_edge": [u, v],
                        "visited": list(visited_set),
                        "unvisited": sorted(list(set(vertices) - visited_set)),
                        "distances": {node: format_dist(d) for node, d in distances.items()},
                        "predecessors": dict(predecessors),
                        "data_structure_state": {"iteration": i, "max_iterations": num_vertices - 1},
                        "highlight_path": [[u, v]],
                        "explanation": f"[Pass {i}] Relaxed edge ({u} → {v}, wt={weight}): distance reduced from {format_dist(old_dist)} to {format_dist(new_dist)}. Predecessor[{v}] = '{u}'."
                    })

        # Early termination optimization: if no distance updated, we converged!
        if not updated_in_this_pass:
            step_num += 1
            steps.append({
                "step_number": step_num,
                "iteration": f"Pass {i} of {num_vertices - 1}",
                "action": "converged",
                "current_vertex": None,
                "current_edge": None,
                "visited": list(visited_set),
                "unvisited": sorted(list(set(vertices) - visited_set)),
                "distances": {node: format_dist(d) for node, d in distances.items()},
                "predecessors": dict(predecessors),
                "data_structure_state": {"iteration": i, "converged": True},
                "highlight_path": [],
                "explanation": f"Convergence reached early at pass {i}! No distances were updated, meaning shortest paths are finalized."
            })
            break

    # Check for negative-weight cycles (Iteration V)
    for u, v, weight in unique_edges:
        if distances[u] != float('inf') and distances[u] + weight < distances[v]:
            negative_cycle_detected = True
            
            # Trace the negative cycle
            curr = v
            for _ in range(num_vertices):
                curr = predecessors[curr] or curr
            cycle_start = curr
            cycle = [cycle_start]
            curr = predecessors[cycle_start]
            while curr and curr != cycle_start and curr not in cycle:
                cycle.append(curr)
                curr = predecessors[curr]
            cycle.append(cycle_start)
            cycle.reverse()
            cycle_nodes = cycle

            step_num += 1
            cycle_edges = [[cycle_nodes[k], cycle_nodes[k+1]] for k in range(len(cycle_nodes) - 1)]
            steps.append({
                "step_number": step_num,
                "iteration": "Negative Cycle Check",
                "action": "negative_cycle",
                "current_vertex": u,
                "current_edge": [u, v],
                "visited": list(visited_set),
                "unvisited": sorted(list(set(vertices) - visited_set)),
                "distances": {node: format_dist(d) for node, d in distances.items()},
                "predecessors": dict(predecessors),
                "data_structure_state": {"negative_cycle": True},
                "highlight_path": cycle_edges,
                "explanation": f"NEGATIVE-WEIGHT CYCLE DETECTED! Edge ({u} → {v}) can still be relaxed. Negative cycle involves vertices: {' → '.join(cycle_nodes)}."
            })
            break

    exec_time = (time.perf_counter() - start_time) * 1000

    if negative_cycle_detected:
        return {
            "success": False,
            "error": f"Negative-weight cycle detected in the graph reachable from '{source}'. Shortest path is undefined because total cost can decrease infinitely.",
            "algorithm": "Bellman-Ford",
            "source": source,
            "destination": destination,
            "path": [],
            "total_distance": None,
            "visited_nodes": list(visited_set),
            "visited_count": len(visited_set),
            "relaxations_count": relaxations_count,
            "execution_time_ms": round(exec_time, 4),
            "time_complexity": "O(V * E)",
            "space_complexity": "O(V)",
            "explanation": f"Bellman-Ford detected a negative-weight cycle reachable from '{source}'. In the presence of negative cycles, a minimum cost path does not exist because one could loop indefinitely through the cycle to reduce path cost to -∞.",
            "steps": steps
        }

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

    step_num += 1
    path_edges = [[path[k], path[k+1]] for k in range(len(path) - 1)] if len(path) > 1 else []

    if path:
        steps.append({
            "step_number": step_num,
            "iteration": "Final Result",
            "action": "completed",
            "current_vertex": destination,
            "current_edge": None,
            "visited": list(visited_set),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {node: format_dist(d) for node, d in distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": {"completed": True},
            "highlight_path": path_edges,
            "explanation": f"Bellman-Ford completed. Shortest path from '{source}' to '{destination}': {' → '.join(path)} with total cost {total_dist}."
        })
        explanation = f"Bellman-Ford verified shortest path from '{source}' to '{destination}': {' → '.join(path)} with total cost {total_dist}. Performed {relaxations_count} edge relaxations with negative cycle verification."
    else:
        steps.append({
            "step_number": step_num,
            "iteration": "Final Result",
            "action": "unreachable",
            "current_vertex": destination,
            "current_edge": None,
            "visited": list(visited_set),
            "unvisited": sorted(list(set(vertices) - visited_set)),
            "distances": {node: format_dist(d) for node, d in distances.items()},
            "predecessors": dict(predecessors),
            "data_structure_state": {"completed": True},
            "highlight_path": [],
            "explanation": f"Destination '{destination}' is unreachable from '{source}'."
        })
        explanation = f"Destination '{destination}' is not reachable from '{source}' in the provided graph."

    return {
        "success": True,
        "error": None,
        "algorithm": "Bellman-Ford",
        "source": source,
        "destination": destination,
        "path": path,
        "total_distance": total_dist,
        "visited_nodes": list(visited_set),
        "visited_count": len(visited_set),
        "relaxations_count": relaxations_count,
        "execution_time_ms": round(exec_time, 4),
        "time_complexity": "O(V * E)",
        "space_complexity": "O(V)",
        "explanation": explanation,
        "steps": steps
    }
