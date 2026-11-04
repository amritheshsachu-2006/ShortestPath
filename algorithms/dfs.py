import time

def run_dfs(vertices, edges, adj, source, destination):
    """
    Depth-First Search (DFS) Traversal Algorithm.
    Explores as deep as possible along each branch before backtracking.
    Finds a path to the destination if connected, but DOES NOT guarantee
    the shortest path in terms of edge count or edge weight.
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    start_time = time.perf_counter()
    steps = []

    visited_set = set()
    visited_order = []
    predecessors = {v: None for v in vertices}
    step_num = 1
    checks_count = 0
    found_path = False

    # Explicit stack to allow step-by-step recording including backtrack
    # Stack stores: (vertex, parent, neighbor_index)
    stack = [(source, None, 0)]
    visited_set.add(source)
    visited_order.append(source)

    steps.append({
        "step_number": step_num,
        "action": "init",
        "current_vertex": source,
        "current_edge": None,
        "visited": list(visited_order),
        "unvisited": sorted(list(set(vertices) - visited_set)),
        "predecessors": dict(predecessors),
        "data_structure_state": [item[0] for item in stack],
        "highlight_path": [],
        "explanation": f"Initialize DFS: Push source '{source}' onto stack. Marked as visited."
    })

    if source == destination:
        found_path = True
    else:
        while stack and not found_path:
            u, parent, nbr_idx = stack[-1]
            neighbors = adj.get(u, [])

            if nbr_idx < len(neighbors):
                neighbor, weight = neighbors[nbr_idx]
                # Increment neighbor pointer for vertex u on stack
                stack[-1] = (u, parent, nbr_idx + 1)
                checks_count += 1
                step_num += 1

                if neighbor not in visited_set:
                    visited_set.add(neighbor)
                    visited_order.append(neighbor)
                    predecessors[neighbor] = u
                    stack.append((neighbor, u, 0))

                    steps.append({
                        "step_number": step_num,
                        "action": "explore_forward",
                        "current_vertex": neighbor,
                        "current_edge": [u, neighbor],
                        "visited": list(visited_order),
                        "unvisited": sorted(list(set(vertices) - visited_set)),
                        "predecessors": dict(predecessors),
                        "data_structure_state": [item[0] for item in stack],
                        "highlight_path": [[stack[i][0], stack[i+1][0]] for i in range(len(stack) - 1)],
                        "explanation": f"Advancing forward along edge ({u} → {neighbor}, wt={weight}). Pushed '{neighbor}' to DFS stack. Predecessor[{neighbor}] = '{u}'."
                    })

                    if neighbor == destination:
                        found_path = True
                        step_num += 1
                        steps.append({
                            "step_number": step_num,
                            "action": "destination_reached",
                            "current_vertex": neighbor,
                            "current_edge": None,
                            "visited": list(visited_order),
                            "unvisited": sorted(list(set(vertices) - visited_set)),
                            "predecessors": dict(predecessors),
                            "data_structure_state": [item[0] for item in stack],
                            "highlight_path": [[stack[i][0], stack[i+1][0]] for i in range(len(stack) - 1)],
                            "explanation": f"Destination '{destination}' reached via depth exploration path."
                        })
                        break
                else:
                    steps.append({
                        "step_number": step_num,
                        "action": "already_visited",
                        "current_vertex": u,
                        "current_edge": [u, neighbor],
                        "visited": list(visited_order),
                        "unvisited": sorted(list(set(vertices) - visited_set)),
                        "predecessors": dict(predecessors),
                        "data_structure_state": [item[0] for item in stack],
                        "highlight_path": [[stack[i][0], stack[i+1][0]] for i in range(len(stack) - 1)],
                        "explanation": f"Neighbor '{neighbor}' is already visited. Skipping edge ({u} → {neighbor})."
                    })
            else:
                # All neighbors explored, backtrack!
                popped = stack.pop()
                step_num += 1
                current_top = stack[-1][0] if stack else None
                steps.append({
                    "step_number": step_num,
                    "action": "backtrack",
                    "current_vertex": current_top,
                    "current_edge": None,
                    "visited": list(visited_order),
                    "unvisited": sorted(list(set(vertices) - visited_set)),
                    "predecessors": dict(predecessors),
                    "data_structure_state": [item[0] for item in stack],
                    "highlight_path": [[stack[i][0], stack[i+1][0]] for i in range(len(stack) - 1)],
                    "explanation": f"All outgoing paths from '{popped[0]}' explored. Backtracking up the recursion stack."
                })

    # Path reconstruction
    path = []
    total_cost = 0
    if found_path:
        curr = destination
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()

        # Calculate sum of weights along DFS discovered path
        for idx in range(len(path) - 1):
            s_node, t_node = path[idx], path[idx+1]
            found_w = 1
            for nbr, w in adj.get(s_node, []):
                if nbr == t_node:
                    found_w = w
                    break
            total_cost += found_w

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
            "predecessors": dict(predecessors),
            "data_structure_state": [],
            "highlight_path": path_edges,
            "explanation": f"DFS finished! Discovered path: {' → '.join(path)} (cost = {total_cost}, hops = {len(path)-1}). Note: DFS does not guarantee an optimal shortest path."
        })
        explanation = f"DFS discovered path from '{source}' to '{destination}': {' → '.join(path)} (total cost = {total_cost}, hops = {len(path)-1}). Explored {len(visited_order)} vertices. DFS is an exhaustive depth traversal algorithm, not an optimization algorithm, so this path is not guaranteed to be shortest."
    else:
        steps.append({
            "step_number": step_num,
            "action": "unreachable",
            "current_vertex": destination,
            "current_edge": None,
            "visited": list(visited_order),
            "unvisited": sorted(list(set(vertices) - visited_set)),
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
        "algorithm": "DFS",
        "source": source,
        "destination": destination,
        "path": path,
        "total_distance": total_cost if path else None,
        "total_hops": len(path) - 1 if path else None,
        "visited_nodes": visited_order,
        "visited_count": len(visited_order),
        "relaxations_count": checks_count,
        "execution_time_ms": round(exec_time, 4),
        "time_complexity": "O(V + E)",
        "space_complexity": "O(V)",
        "explanation": explanation,
        "steps": steps
    }

