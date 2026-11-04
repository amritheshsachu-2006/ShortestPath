import pytest
import os
import tempfile
import json
from app import app
from database.database import init_db
from utils.graph_utils import (
    parse_cytoscape_graph,
    validate_graph_payload,
    get_sample_graphs,
    generate_random_graph
)

@pytest.fixture
def auth_client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-graph-key-54321'
    os.environ['DATABASE_PATH'] = db_path

    with app.app_context():
        init_db(db_path)

    with app.test_client() as client:
        # Register and login user
        client.post('/register', data={
            'full_name': 'Graph Tester',
            'username': 'graphtester',
            'email': 'tester@college.edu',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        yield client

    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)

def test_parse_cytoscape_graph():
    elements = {
        "nodes": [
            {"data": {"id": "X", "label": "X"}},
            {"data": {"id": "Y", "label": "Y"}},
            {"data": {"id": "Z", "label": "Z"}}
        ],
        "edges": [
            {"data": {"id": "e1", "source": "X", "target": "Y", "weight": 5}},
            {"data": {"id": "e2", "source": "Y", "target": "Z", "weight": -3}}
        ]
    }
    vertices, edges, adj, directed = parse_cytoscape_graph(elements, directed=True)
    assert vertices == ["X", "Y", "Z"]
    assert len(edges) == 2
    assert adj["X"] == [("Y", 5)]
    assert adj["Y"] == [("Z", -3)]

def test_parse_undirected_graph():
    elements = [
        {"data": {"id": "1"}},
        {"data": {"id": "2"}},
        {"data": {"source": "1", "target": "2", "weight": 10}}
    ]
    vertices, edges, adj, directed = parse_cytoscape_graph(elements, directed=False)
    assert vertices == ["1", "2"]
    # For undirected graph, both 1->2 and 2->1 should be present in adjacency
    assert ("2", 10) in adj["1"]
    assert ("1", 10) in adj["2"]

def test_validate_graph_payload():
    # Empty vertices
    valid, msg = validate_graph_payload([], [])
    assert valid is False
    assert "at least one vertex" in msg

    # Missing source
    valid, msg = validate_graph_payload(["A", "B"], [], source="C", destination="B")
    assert valid is False
    assert "Source vertex 'C' does not exist" in msg

    # Missing destination
    valid, msg = validate_graph_payload(["A", "B"], [], source="A", destination="Z")
    assert valid is False
    assert "Destination vertex 'Z' does not exist" in msg

    # Valid graph
    valid, msg = validate_graph_payload(["A", "B"], [], source="A", destination="B")
    assert valid is True
    assert msg is None

def test_get_sample_graphs():
    samples = get_sample_graphs()
    assert "classic_6" in samples
    assert "negative_dag" in samples
    assert "negative_cycle" in samples
    assert "undirected_web" in samples
    assert "all_pairs_4" in samples
    assert "disconnected" in samples

    for key, item in samples.items():
        assert "name" in item
        assert "elements" in item

def test_generate_random_graph():
    graph = generate_random_graph(num_nodes=5, density=0.5, directed=True, allow_negative=False)
    assert len(graph["elements"]["nodes"]) == 5
    assert len(graph["elements"]["edges"]) >= 4  # Backbone guaranteed

def test_save_and_load_graph_api(auth_client):
    sample = get_sample_graphs()["classic_6"]
    # Save graph
    resp = auth_client.post('/api/graphs', json={
        "graph_name": "My Custom Network",
        "graph_data": sample
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    graph_id = data["graph_id"]

    # Get graphs list
    list_resp = auth_client.get('/api/graphs')
    list_data = list_resp.get_json()
    assert list_data["success"] is True
    assert any(g["id"] == graph_id for g in list_data["graphs"])

    # Load specific graph
    load_resp = auth_client.get(f'/api/graphs/{graph_id}')
    load_data = load_resp.get_json()
    assert load_data["success"] is True
    assert load_data["graph"]["graph_name"] == "My Custom Network"

    # Delete graph
    del_resp = auth_client.delete(f'/api/graphs/{graph_id}')
    assert del_resp.status_code == 200
    assert del_resp.get_json()["success"] is True

def test_search_history_api(auth_client):
    # Run algorithm search through API which logs to history
    sample = get_sample_graphs()["classic_6"]
    run_resp = auth_client.post('/api/algorithm/run', json={
        "algorithm": "dijkstra",
        "source": "A",
        "destination": "F",
        "graph_data": sample["elements"],
        "directed": True,
        "save_to_history": True
    })
    assert run_resp.status_code == 200
    assert run_resp.get_json()["success"] is True

    # Check history endpoint
    hist_resp = auth_client.get('/api/history')
    hist_data = hist_resp.get_json()
    assert hist_data["success"] is True
    assert len(hist_data["history"]) >= 1
    assert hist_data["history"][0]["source"] == "A"
    assert hist_data["history"][0]["destination"] == "F"

    # Clear history
    clear_resp = auth_client.delete('/api/history')
    assert clear_resp.status_code == 200
    assert clear_resp.get_json()["success"] is True

    # Verify history is empty
    empty_hist = auth_client.get('/api/history').get_json()
    assert len(empty_hist["history"]) == 0

