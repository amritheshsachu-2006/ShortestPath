import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# ==============================================================================
# ZERO-DATABASE IN-MEMORY DATA STORE (Optimized for Vercel Serverless & Local)
# No SQLite file locks, no read-only file system errors on cloud hosting.
# ==============================================================================

_users = {}              # id -> user dict
_users_by_username = {}  # lowercase username -> user dict
_users_by_email = {}     # lowercase email -> user dict
_graphs = {}             # id -> graph dict
_search_history = []     # list of history records

_user_id_counter = 1
_graph_id_counter = 1
_history_id_counter = 1

def get_db_connection(db_path=None):
    """Compatibility stub for raw connection requests."""
    return None

def init_db(db_path=None):
    """
    Initialize in-memory data store.
    Pre-seeds default student and administrator demo credentials.
    """
    global _users, _users_by_username, _users_by_email, _graphs, _search_history
    global _user_id_counter, _graph_id_counter, _history_id_counter

    # If an explicit db_path is provided (e.g. during test fixtures), reset for a clean test run
    if db_path is not None:
        _users = {}
        _users_by_username = {}
        _users_by_email = {}
        _graphs = {}
        _search_history = []
        _user_id_counter = 1
        _graph_id_counter = 1
        _history_id_counter = 1

    # Pre-seed demo accounts if not already present
    if "admin" not in _users_by_username:
        create_user("Admin User", "admin", "admin@college.edu", generate_password_hash("password123"))
    if "student" not in _users_by_username:
        create_user("Student Demo", "student", "student@college.edu", generate_password_hash("password123"))
    if "demo" not in _users_by_username:
        create_user("Demo User", "demo", "demo@college.edu", generate_password_hash("password123"))

# ==========================================
# USER MANAGEMENT
# ==========================================

def create_user(full_name, username, email, password_hash, db_path=None):
    """Create a new user record in memory."""
    global _user_id_counter
    u_clean = username.strip().lower()
    e_clean = email.strip().lower()

    if u_clean in _users_by_username:
        raise sqlite3.IntegrityError(f"UNIQUE constraint failed: users.username '{u_clean}'")
    if e_clean in _users_by_email:
        raise sqlite3.IntegrityError(f"UNIQUE constraint failed: users.email '{e_clean}'")

    user_id = _user_id_counter
    _user_id_counter += 1

    user_record = {
        "id": user_id,
        "full_name": full_name.strip(),
        "username": u_clean,
        "email": e_clean,
        "password_hash": password_hash,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    _users[user_id] = user_record
    _users_by_username[u_clean] = user_record
    _users_by_email[e_clean] = user_record

    return user_id

def get_user_by_username(username, db_path=None):
    """Retrieve user by case-insensitive username."""
    if not username:
        return None
    user = _users_by_username.get(username.strip().lower())
    return dict(user) if user else None

def get_user_by_email(email, db_path=None):
    """Retrieve user by case-insensitive email."""
    if not email:
        return None
    user = _users_by_email.get(email.strip().lower())
    return dict(user) if user else None

def get_user_by_id(user_id, db_path=None):
    """Retrieve user by ID."""
    user = _users.get(user_id)
    return dict(user) if user else None

def reset_password_by_username_or_email(identifier, new_password_hash, db_path=None):
    """Update user password in memory."""
    if not identifier:
        return False
    target = identifier.strip().lower()
    user = _users_by_username.get(target) or _users_by_email.get(target)
    if user:
        user["password_hash"] = new_password_hash
        return True
    return False

# ==========================================
# GRAPH TOPOLOGY STORAGE
# ==========================================

def save_graph(user_id, graph_name, graph_data_json, db_path=None):
    """Save or update a graph topology for a specific user."""
    global _graph_id_counter
    g_name = graph_name.strip()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Check if a graph with this name already exists for this user
    for gid, g in _graphs.items():
        if g["user_id"] == user_id and g["graph_name"] == g_name:
            g["graph_data"] = graph_data_json
            g["updated_at"] = now_str
            return gid

    graph_id = _graph_id_counter
    _graph_id_counter += 1

    _graphs[graph_id] = {
        "id": graph_id,
        "user_id": user_id,
        "graph_name": g_name,
        "graph_data": graph_data_json,
        "created_at": now_str,
        "updated_at": now_str
    }
    return graph_id

def get_user_graphs(user_id, db_path=None):
    """Fetch all saved graphs belonging to the specified user."""
    user_graphs = [
        {
            "id": g["id"],
            "graph_name": g["graph_name"],
            "created_at": g["created_at"],
            "updated_at": g["updated_at"]
        }
        for g in _graphs.values()
        if g["user_id"] == user_id
    ]
    user_graphs.sort(key=lambda x: x["updated_at"], reverse=True)
    return user_graphs

def get_graph_by_id(graph_id, user_id, db_path=None):
    """Fetch specific graph by ID and owner."""
    g = _graphs.get(graph_id)
    if g and g["user_id"] == user_id:
        return dict(g)
    return None

def delete_graph(graph_id, user_id, db_path=None):
    """Delete a user's graph."""
    g = _graphs.get(graph_id)
    if g and g["user_id"] == user_id:
        del _graphs[graph_id]
        return True
    return False

# ==========================================
# SEARCH HISTORY MANAGEMENT
# ==========================================

def add_search_history(user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, db_path=None):
    """Log an algorithm search execution in memory."""
    global _history_id_counter
    hist_id = _history_id_counter
    _history_id_counter += 1

    entry = {
        "id": hist_id,
        "user_id": user_id,
        "source": source,
        "destination": destination,
        "algorithm": algorithm,
        "shortest_path": shortest_path,
        "total_distance": total_distance,
        "execution_time": execution_time,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    _search_history.append(entry)
    return hist_id

def get_user_search_history(user_id, limit=100, db_path=None):
    """Retrieve search history for a user sorted by timestamp descending."""
    user_history = [dict(h) for h in _search_history if h["user_id"] == user_id]
    user_history.sort(key=lambda x: x["created_at"], reverse=True)
    return user_history[:limit]

def clear_user_search_history(user_id, db_path=None):
    """Clear all search history for a user."""
    global _search_history
    initial_count = len(_search_history)
    _search_history = [h for h in _search_history if h["user_id"] != user_id]
    return initial_count - len(_search_history)

def get_user_history_stats(user_id, db_path=None):
    """Generate dashboard statistics for a user."""
    user_history = [h for h in _search_history if h["user_id"] == user_id]
    user_history.sort(key=lambda x: x["created_at"], reverse=True)

    algorithm_counts = {}
    for h in user_history:
        algo = h["algorithm"]
        algorithm_counts[algo] = algorithm_counts.get(algo, 0) + 1

    return {
        "total_searches": len(user_history),
        "algorithm_counts": algorithm_counts,
        "recent_searches": [dict(h) for h in user_history[:5]]
    }
