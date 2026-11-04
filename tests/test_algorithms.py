import pytest
from utils.graph_utils import parse_cytoscape_graph, get_sample_graphs
from algorithms import (
    run_dijkstra,
    run_bellman_ford,
    run_floyd_warshall,
    run_bfs,
    run_dfs,
    compare_all_algorithms
)

@pytest.fixture
def classic_graph():
    samples = get_sample_graphs()
    return parse_cytoscape_graph(samples["classic_6"]["elements"], directed=True)

@pytest.fixture
def negative_dag_graph():
    samples = get_sample_graphs()
    return parse_cytoscape_graph(samples["negative_dag"]["elements"], directed=True)

@pytest.fixture
def negative_cycle_graph():
    samples = get_sample_graphs()
    return parse_cytoscape_graph(samples["negative_cycle"]["elements"], directed=True)

@pytest.fixture
def disconnected_graph():
    samples = get_sample_graphs()
    return parse_cytoscape_graph(samples["disconnected"]["elements"], directed=False)

# 1. Dijkstra Tests
def test_dijkstra_success(classic_graph):
    vertices, edges, adj, _ = classic_graph
    result = run_dijkstra(vertices, edges, adj, "A", "F")
    assert result["success"] is True
    assert result["error"] is None
    # For classic 6 graph:
    # A -> C (2) -> E (10) -> F (3) = 15
    # A -> B (4) -> D (5) -> F (6) = 15
    # A -> C (2) -> D? C->D is 8 (2+8+6=16). B->C is 1: A->B (4) + B->C (1) + C->D(8)...
    # A -> B (4) -> D (5) -> E (2) -> F (3) = 4 + 5 + 2 + 3 = 14!
    # Wait, A->C is 2, C->E is 10.
    # What about A->B->D->E->F = 4+5+2+3 = 14.
    # Or A->C=2, C->D=8 (sum 10), D->E=2 (12), E->F=3 (15).
    # Let's verify result has path starting at A and ending at F:
    assert result["path"][0] == "A"
    assert result["path"][-1] == "F"
    assert result["total_distance"] == 14
    assert len(result["steps"]) > 0

def test_dijkstra_negative_edge_rejection(negative_dag_graph):
    vertices, edges, adj, _ = negative_dag_graph
    result = run_dijkstra(vertices, edges, adj, "S", "T")
    assert result["success"] is False
    assert "Negative edge weight detected" in result["error"]

def test_dijkstra_unreachable(disconnected_graph):
    vertices, edges, adj, _ = disconnected_graph
    result = run_dijkstra(vertices, edges, adj, "A", "F")
    assert result["success"] is True
    assert result["path"] == []
    assert result["total_distance"] is None
    assert "not reachable" in result["explanation"] or "unreachable" in result["explanation"]

# 2. Bellman-Ford Tests
def test_bellman_ford_negative_weights(negative_dag_graph):
    vertices, edges, adj, _ = negative_dag_graph
    result = run_bellman_ford(vertices, edges, adj, "S", "T")
    assert result["success"] is True
    assert result["error"] is None
    assert result["path"][0] == "S"
    assert result["path"][-1] == "T"
    assert result["total_distance"] is not None
    # Path: S -> B (6) -> A (-2) -> C (-3) -> D (2) -> T (-1) = 2
    assert result["total_distance"] == 2

def test_bellman_ford_negative_cycle_detection(negative_cycle_graph):
    vertices, edges, adj, _ = negative_cycle_graph
    result = run_bellman_ford(vertices, edges, adj, "A", "E")
    assert result["success"] is False
    assert "Negative-weight cycle detected" in result["error"]

# 3. Floyd-Warshall Tests
def test_floyd_warshall_all_pairs(classic_graph):
    vertices, edges, adj, _ = classic_graph
    result = run_floyd_warshall(vertices, edges, adj, "A", "F")
    assert result["success"] is True
    assert result["path"] == ["A", "B", "D", "E", "F"]
    assert result["total_distance"] == 14
    assert "matrix" in result
    assert result["matrix"]["A"]["F"] == 14

def test_floyd_warshall_negative_cycle(negative_cycle_graph):
    vertices, edges, adj, _ = negative_cycle_graph
    result = run_floyd_warshall(vertices, edges, adj, "A", "E")
    assert result["success"] is False
    assert "Negative-weight cycle detected" in result["error"]

# 4. BFS Tests
def test_bfs_minimum_hops(classic_graph):
    vertices, edges, adj, _ = classic_graph
    result = run_bfs(vertices, edges, adj, "A", "F")
    assert result["success"] is True
    assert result["path"][0] == "A"
    assert result["path"][-1] == "F"
    # Minimum hop paths from A to F:
    # A -> B -> D -> F is 3 hops
    # A -> C -> E -> F is 3 hops
    assert result["total_hops"] == 3
    assert len(result["steps"]) > 0

# 5. DFS Tests
def test_dfs_traversal(classic_graph):
    vertices, edges, adj, _ = classic_graph
    result = run_dfs(vertices, edges, adj, "A", "F")
    assert result["success"] is True
    assert result["path"][0] == "A"
    assert result["path"][-1] == "F"
    assert len(result["visited_nodes"]) > 0

# 6. Comparison runner test
def test_compare_all_algorithms(classic_graph):
    vertices, edges, adj, _ = classic_graph
    results = compare_all_algorithms(vertices, edges, adj, "A", "F")
    assert "dijkstra" in results
    assert "bellman_ford" in results
    assert "floyd_warshall" in results
    assert "bfs" in results
    assert "dfs" in results
    assert results["dijkstra"]["success"] is True
    assert results["bellman_ford"]["success"] is True
    assert results["floyd_warshall"]["success"] is True
