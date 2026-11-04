import sqlite3
import os
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'shortest_path.db')

def get_db_connection(db_path=None):
    """Establish a connection to the SQLite database with Row factory and FK enforcement."""
    path = db_path or os.environ.get('DATABASE_PATH', DEFAULT_DB_PATH)
    # Ensure directory exists
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
        
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=None):
    """Initialize database tables according to specifications."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Graphs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graphs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            graph_name TEXT NOT NULL,
            graph_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Search history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            shortest_path TEXT NOT NULL,
            total_distance REAL,
            execution_time REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_graphs_user_id ON graphs(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user_id ON search_history(user_id);")

    conn.commit()
    conn.close()

# User Management Functions
def create_user(full_name, username, email, password_hash, db_path=None):
    """Insert a new user. Returns user id or raises sqlite3.IntegrityError."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (full_name, username, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (full_name.strip(), username.strip().lower(), email.strip().lower(), password_hash, datetime.utcnow()))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user_by_username(username, db_path=None):
    """Fetch user record by username (case-insensitive)."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_email(email, db_path=None):
    """Fetch user record by email (case-insensitive)."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id, db_path=None):
    """Fetch user record by ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def reset_password_by_username_or_email(identifier, new_password_hash, db_path=None):
    """Update user password given either username or email."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    target = identifier.strip().lower()
    cursor.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE LOWER(username) = ? OR LOWER(email) = ?
    """, (new_password_hash, target, target))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# Graph Management Functions
def save_graph(user_id, graph_name, graph_data_json, db_path=None):
    """Save or update a graph for a specific user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    # Check if a graph with this name already exists for this user
    cursor.execute("SELECT id FROM graphs WHERE user_id = ? AND graph_name = ?", (user_id, graph_name.strip()))
    existing = cursor.fetchone()
    now = datetime.utcnow()
    if existing:
        graph_id = existing['id']
        cursor.execute("""
            UPDATE graphs
            SET graph_data = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (graph_data_json, now, graph_id, user_id))
    else:
        cursor.execute("""
            INSERT INTO graphs (user_id, graph_name, graph_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, graph_name.strip(), graph_data_json, now, now))
        graph_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return graph_id

def get_user_graphs(user_id, db_path=None):
    """Return all graphs saved by the user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, graph_name, created_at, updated_at
        FROM graphs
        WHERE user_id = ?
        ORDER BY updated_at DESC
    """, (user_id,))
    graphs = cursor.fetchall()
    conn.close()
    return [dict(g) for g in graphs]

def get_graph_by_id(graph_id, user_id, db_path=None):
    """Return specific graph by id, ensuring it belongs to the user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM graphs WHERE id = ? AND user_id = ?
    """, (graph_id, user_id))
    graph = cursor.fetchone()
    conn.close()
    return dict(graph) if graph else None

def delete_graph(graph_id, user_id, db_path=None):
    """Delete a user's graph."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM graphs WHERE id = ? AND user_id = ?", (graph_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# Search History Functions
def add_search_history(user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, db_path=None):
    """Record a path search result in history."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO search_history (user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, datetime.utcnow()))
    history_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return history_id

def get_user_search_history(user_id, limit=100, db_path=None):
    """Fetch search history for a user, sorted descending by created_at."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at
        FROM search_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_user_search_history(user_id, db_path=None):
    """Clear all search history for a user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected

def get_user_history_stats(user_id, db_path=None):
    """Retrieve statistical summary for dashboard."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Total searches
    cursor.execute("SELECT COUNT(*) as count FROM search_history WHERE user_id = ?", (user_id,))
    total_searches = cursor.fetchone()['count']
    
    # Searches per algorithm
    cursor.execute("""
        SELECT algorithm, COUNT(*) as count
        FROM search_history
        WHERE user_id = ?
        GROUP BY algorithm
    """, (user_id,))
    algorithm_counts = {row['algorithm']: row['count'] for row in cursor.fetchall()}
    
    # Recent searches (last 5)
    cursor.execute("""
        SELECT id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at
        FROM search_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, (user_id,))
    recent = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {
        "total_searches": total_searches,
        "algorithm_counts": algorithm_counts,
        "recent_searches": recent
    }

