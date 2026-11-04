import random

def parse_cytoscape_graph(graph_data, directed=True):
    """
    Parses Cytoscape.js format data into python structures.
    Supports either:
    1. {"elements": [...] or {"nodes": [...], "edges": [...]}}
    2. list of element objects [{"data": {"id": "A"}}, {"data": {"source": "A", "target": "B", "weight": 5}}]
    3. {"nodes": [...], "edges": [...], "directed": bool}
    
    Returns:
        vertices: sorted list of string vertex ids
        edges: list of tuples (source, target, weight, directed)
        adj: dict mapping vertex -> list of (neighbor, weight)
        is_directed: bool
    """
    if not graph_data:
        return [], [], {}, directed

    # Extract elements
    elements = graph_data
    if isinstance(graph_data, dict):
        if "elements" in graph_data:
            elements = graph_data["elements"]
        elif "nodes" in graph_data and "edges" in graph_data:
            elements = graph_data["nodes"] + graph_data["edges"]
        if "directed" in graph_data:
            directed = bool(graph_data["directed"])

    nodes_list = []
    edges_list = []

    if isinstance(elements, dict):
        nodes_list = elements.get("nodes", [])
        edges_list = elements.get("edges", [])
    elif isinstance(elements, list):
        for el in elements:
            if not isinstance(el, dict):
                continue
            data = el.get("data", el)
            if "source" in data and "target" in data:
                edges_list.append(el)
            elif "id" in data:
                nodes_list.append(el)

    vertices = set()
    for n in nodes_list:
        data = n.get("data", n)
        nid = str(data.get("id") or data.get("label") or "").strip()
        if nid:
            vertices.add(nid)

    edges = []
    adj = {v: [] for v in vertices}

    for e in edges_list:
        data = e.get("data", e)
        src = str(data.get("source", "")).strip()
        tgt = str(data.get("target", "")).strip()
        if not src or not tgt:
            continue
        
        # Ensure vertices exist even if node element was omitted
        vertices.add(src)
        vertices.add(tgt)
        if src not in adj:
            adj[src] = []
        if tgt not in adj:
            adj[tgt] = []

        raw_weight = data.get("weight")
        try:
            if raw_weight is None or raw_weight == "":
                weight = 1.0
            else:
                weight = float(raw_weight)
                # Keep as int if it has no fractional part for cleaner display
                if weight.is_integer():
                    weight = int(weight)
        except (ValueError, TypeError):
            weight = 1.0

        # Check edge directed flag override if specified in edge data
        edge_directed = data.get("directed", directed)

        edges.append((src, tgt, weight, edge_directed))
        adj[src].append((tgt, weight))
        if not edge_directed:
            adj[tgt].append((src, weight))

    sorted_vertices = sorted(list(vertices))
    return sorted_vertices, edges, adj, directed

def validate_graph_payload(vertices, edges, source=None, destination=None):
    """
    Validates graph structure and source/destination endpoints.
    Returns (is_valid, error_message).
    """
    if not vertices:
        return False, "The graph contains no vertices. Please add at least one vertex."
    
    if source is not None and source not in vertices:
        return False, f"Source vertex '{source}' does not exist in the graph."
        
    if destination is not None and destination not in vertices:
        return False, f"Destination vertex '{destination}' does not exist in the graph."

    return True, None

def get_sample_graphs():
    """
    Returns predefined educational sample graphs.
    """
    return {
        "classic_6": {
            "name": "Classic 6-Vertex Network (Positive Weights)",
            "description": "Standard pedagogical graph for Dijkstra, BFS and DFS with positive weights.",
            "directed": True,
            "elements": {
                "nodes": [
                    {"data": {"id": "A", "label": "A"}, "position": {"x": 100, "y": 200}},
                    {"data": {"id": "B", "label": "B"}, "position": {"x": 250, "y": 100}},
                    {"data": {"id": "C", "label": "C"}, "position": {"x": 250, "y": 300}},
                    {"data": {"id": "D", "label": "D"}, "position": {"x": 420, "y": 100}},
                    {"data": {"id": "E", "label": "E"}, "position": {"x": 420, "y": 300}},
                    {"data": {"id": "F", "label": "F"}, "position": {"x": 580, "y": 200}}
                ],
                "edges": [
                    {"data": {"id": "e_A_B", "source": "A", "target": "B", "weight": 4, "directed": True}},
                    {"data": {"id": "e_A_C", "source": "A", "target": "C", "weight": 2, "directed": True}},
                    {"data": {"id": "e_B_C", "source": "B", "target": "C", "weight": 1, "directed": True}},
                    {"data": {"id": "e_B_D", "source": "B", "target": "D", "weight": 5, "directed": True}},
                    {"data": {"id": "e_C_D", "source": "C", "target": "D", "weight": 8, "directed": True}},
                    {"data": {"id": "e_C_E", "source": "C", "target": "E", "weight": 10, "directed": True}},
                    {"data": {"id": "e_D_E", "source": "D", "target": "E", "weight": 2, "directed": True}},
                    {"data": {"id": "e_D_F", "source": "D", "target": "F", "weight": 6, "directed": True}},
                    {"data": {"id": "e_E_F", "source": "E", "target": "F", "weight": 3, "directed": True}}
                ]
            }
        },
        "negative_dag": {
            "name": "Negative-Edge DAG (No Negative Cycle)",
            "description": "Demonstrates Bellman-Ford correctly handling negative weights on an acyclic graph.",
            "directed": True,
            "elements": {
                "nodes": [
                    {"data": {"id": "S", "label": "S"}, "position": {"x": 100, "y": 200}},
                    {"data": {"id": "A", "label": "A"}, "position": {"x": 260, "y": 100}},
                    {"data": {"id": "B", "label": "B"}, "position": {"x": 260, "y": 300}},
                    {"data": {"id": "C", "label": "C"}, "position": {"x": 440, "y": 100}},
                    {"data": {"id": "D", "label": "D"}, "position": {"x": 440, "y": 300}},
                    {"data": {"id": "T", "label": "T"}, "position": {"x": 600, "y": 200}}
                ],
                "edges": [
                    {"data": {"id": "e_S_A", "source": "S", "target": "A", "weight": 7, "directed": True}},
                    {"data": {"id": "e_S_B", "source": "S", "target": "B", "weight": 6, "directed": True}},
                    {"data": {"id": "e_A_C", "source": "A", "target": "C", "weight": -3, "directed": True}},
                    {"data": {"id": "e_B_A", "source": "B", "target": "A", "weight": -2, "directed": True}},
                    {"data": {"id": "e_B_D", "source": "B", "target": "D", "weight": 9, "directed": True}},
                    {"data": {"id": "e_C_T", "source": "C", "target": "T", "weight": 4, "directed": True}},
                    {"data": {"id": "e_D_T", "source": "D", "target": "T", "weight": -1, "directed": True}},
                    {"data": {"id": "e_C_D", "source": "C", "target": "D", "weight": 2, "directed": True}}
                ]
            }
        },
        "negative_cycle": {
            "name": "Negative-Weight Cycle Demo",
            "description": "Contains a negative cycle (B -> C -> D -> B with sum -2). Tests cycle detection in Bellman-Ford & Floyd-Warshall.",
            "directed": True,
            "elements": {
                "nodes": [
                    {"data": {"id": "A", "label": "A"}, "position": {"x": 120, "y": 200}},
                    {"data": {"id": "B", "label": "B"}, "position": {"x": 280, "y": 120}},
                    {"data": {"id": "C", "label": "C"}, "position": {"x": 460, "y": 120}},
                    {"data": {"id": "D", "label": "D"}, "position": {"x": 370, "y": 280}},
                    {"data": {"id": "E", "label": "E"}, "position": {"x": 580, "y": 200}}
                ],
                "edges": [
                    {"data": {"id": "e_A_B", "source": "A", "target": "B", "weight": 4, "directed": True}},
                    {"data": {"id": "e_B_C", "source": "B", "target": "C", "weight": 1, "directed": True}},
                    {"data": {"id": "e_C_D", "source": "C", "target": "D", "weight": -5, "directed": True}},
                    {"data": {"id": "e_D_B", "source": "D", "target": "B", "weight": 2, "directed": True}},
                    {"data": {"id": "e_C_E", "source": "C", "target": "E", "weight": 3, "directed": True}}
                ]
            }
        },
        "undirected_web": {
            "name": "Undirected Multi-Path Web",
            "description": "Ideal for comparing BFS minimum-edge traversal vs weighted shortest paths.",
            "directed": False,
            "elements": {
                "nodes": [
                    {"data": {"id": "1", "label": "1"}, "position": {"x": 100, "y": 200}},
                    {"data": {"id": "2", "label": "2"}, "position": {"x": 240, "y": 100}},
                    {"data": {"id": "3", "label": "3"}, "position": {"x": 240, "y": 300}},
                    {"data": {"id": "4", "label": "4"}, "position": {"x": 400, "y": 100}},
                    {"data": {"id": "5", "label": "5"}, "position": {"x": 400, "y": 300}},
                    {"data": {"id": "6", "label": "6"}, "position": {"x": 550, "y": 200}}
                ],
                "edges": [
                    {"data": {"id": "e_1_2", "source": "1", "target": "2", "weight": 10, "directed": False}},
                    {"data": {"id": "e_1_3", "source": "1", "target": "3", "weight": 1, "directed": False}},
                    {"data": {"id": "e_2_4", "source": "2", "target": "4", "weight": 10, "directed": False}},
                    {"data": {"id": "e_3_5", "source": "3", "target": "5", "weight": 1, "directed": False}},
                    {"data": {"id": "e_4_6", "source": "4", "target": "6", "weight": 10, "directed": False}},
                    {"data": {"id": "e_5_6", "source": "5", "target": "6", "weight": 1, "directed": False}},
                    {"data": {"id": "e_1_6", "source": "1", "target": "6", "weight": 50, "directed": False}}
                ]
            }
        },
        "all_pairs_4": {
            "name": "All-Pairs 4-City Network",
            "description": "Dense network designed for Floyd-Warshall all-pairs shortest paths matrix examination.",
            "directed": True,
            "elements": {
                "nodes": [
                    {"data": {"id": "CityA", "label": "City A"}, "position": {"x": 150, "y": 120}},
                    {"data": {"id": "CityB", "label": "City B"}, "position": {"x": 450, "y": 120}},
                    {"data": {"id": "CityC", "label": "City C"}, "position": {"x": 450, "y": 320}},
                    {"data": {"id": "CityD", "label": "City D"}, "position": {"x": 150, "y": 320}}
                ],
                "edges": [
                    {"data": {"id": "e_AB", "source": "CityA", "target": "CityB", "weight": 3, "directed": True}},
                    {"data": {"id": "e_BC", "source": "CityB", "target": "CityC", "weight": 1, "directed": True}},
                    {"data": {"id": "e_CD", "source": "CityC", "target": "CityD", "weight": 7, "directed": True}},
                    {"data": {"id": "e_DA", "source": "CityD", "target": "CityA", "weight": 2, "directed": True}},
                    {"data": {"id": "e_AC", "source": "CityA", "target": "CityC", "weight": 8, "directed": True}},
                    {"data": {"id": "e_BD", "source": "CityB", "target": "CityD", "weight": 4, "directed": True}}
                ]
            }
        },
        "disconnected": {
            "name": "Disconnected Components Graph",
            "description": "Two separate components (A-B-C and D-E-F) to test unreachable path detection.",
            "directed": False,
            "elements": {
                "nodes": [
                    {"data": {"id": "A", "label": "A"}, "position": {"x": 120, "y": 150}},
                    {"data": {"id": "B", "label": "B"}, "position": {"x": 240, "y": 100}},
                    {"data": {"id": "C", "label": "C"}, "position": {"x": 240, "y": 200}},
                    {"data": {"id": "D", "label": "D"}, "position": {"x": 440, "y": 150}},
                    {"data": {"id": "E", "label": "E"}, "position": {"x": 560, "y": 100}},
                    {"data": {"id": "F", "label": "F"}, "position": {"x": 560, "y": 200}}
                ],
                "edges": [
                    {"data": {"id": "e_AB", "source": "A", "target": "B", "weight": 3, "directed": False}},
                    {"data": {"id": "e_BC", "source": "B", "target": "C", "weight": 4, "directed": False}},
                    {"data": {"id": "e_AC", "source": "A", "target": "C", "weight": 5, "directed": False}},
                    {"data": {"id": "e_DE", "source": "D", "target": "E", "weight": 2, "directed": False}},
                    {"data": {"id": "e_EF", "source": "E", "target": "F", "weight": 3, "directed": False}}
                ]
            }
        }
    }

def generate_random_graph(num_nodes=6, density=0.4, directed=True, allow_negative=False):
    """
    Generates a connected or semi-dense random graph with pleasant layout coordinates.
    """
    num_nodes = max(3, min(num_nodes, 12))
    labels = [chr(65 + i) for i in range(num_nodes)]  # A, B, C, ...
    
    nodes = []
    import math
    center_x = 350
    center_y = 220
    radius = 160

    for i, label in enumerate(labels):
        angle = (2 * math.pi * i) / num_nodes
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        nodes.append({
            "data": {"id": label, "label": label},
            "position": {"x": x, "y": y}
        })

    edges = []
    edge_set = set()

    # First ensure a connected backbone
    for i in range(num_nodes - 1):
        u = labels[i]
        v = labels[i + 1]
        weight = random.randint(1, 9) if not allow_negative else random.randint(-2, 9)
        if weight == 0:
            weight = 1
        edge_id = f"e_{u}_{v}"
        edges.append({
            "data": {"id": edge_id, "source": u, "target": v, "weight": weight, "directed": directed}
        })
        edge_set.add((u, v))
        if not directed:
            edge_set.add((v, u))

    # Add additional random edges based on density
    for u in labels:
        for v in labels:
            if u != v and (u, v) not in edge_set:
                if random.random() < density:
                    weight = random.randint(1, 10) if not allow_negative else random.randint(-3, 10)
                    if weight == 0:
                        weight = 2
                    edge_id = f"e_{u}_{v}_{random.randint(100, 999)}"
                    edges.append({
                        "data": {"id": edge_id, "source": u, "target": v, "weight": weight, "directed": directed}
                    })
                    edge_set.add((u, v))
                    if not directed:
                        edge_set.add((v, u))

    return {
        "directed": directed,
        "elements": {
            "nodes": nodes,
            "edges": edges
        }
    }

