import os
import sys
import tempfile
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# ==============================================================================
# UNIVERSAL DATABASE LAYER (PostgreSQL / Supabase + Serverless SQLite)
# Fully compatible with Vercel Serverless (Read-only container /tmp safety)
# and Local Development across Windows, macOS, and Linux.
# ==============================================================================

def get_database_url():
    """Returns database URL if configured, converting legacy postgres:// to postgresql://."""
    url = os.environ.get('DATABASE_URL')
    if url and url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url

def get_sqlite_path(db_path=None):
    """
    Safely resolves SQLite database path.
    On Vercel and cloud serverless platforms, directories outside /tmp are read-only.
    This dynamically selects a writable path so 'unable to open database file' never occurs.
    """
    if db_path:
        return db_path
    if os.environ.get('DATABASE_PATH'):
        return os.environ.get('DATABASE_PATH')

    # If running on Vercel or other serverless platforms
    if os.environ.get('VERCEL') == '1' or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        tmp_dir = tempfile.gettempdir()
        return os.path.join(tmp_dir, 'shortest_path.db')

    # Check if local directory is writable
    local_dir = os.path.abspath(os.path.dirname(__file__))
    try:
        os.makedirs(local_dir, exist_ok=True)
        test_path = os.path.join(local_dir, '.write_check')
        with open(test_path, 'w') as f:
            f.write('1')
        os.remove(test_path)
        return os.path.join(local_dir, 'shortest_path.db')
    except (OSError, IOError, PermissionError):
        # Read-only filesystem detected (e.g. cloud container) - fall back to /tmp
        tmp_dir = tempfile.gettempdir()
        return os.path.join(tmp_dir, 'shortest_path.db')

def get_db_connection(db_path=None):
    """
    Establishes connection to either PostgreSQL (Supabase) or SQLite.
    Returns (conn, is_postgres).
    """
    db_url = get_database_url()

    # 1. Try PostgreSQL (Supabase / Neon / Vercel Postgres) if configured
    if db_url and not db_path:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            return conn, True
        except Exception as e:
            print(f"[Database] PostgreSQL connection failed, falling back to SQLite: {e}", file=sys.stderr)

    # 2. Serverless-safe SQLite fallback
    path = get_sqlite_path(db_path)
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name, exist_ok=True)
        except OSError:
            path = os.path.join(tempfile.gettempdir(), 'shortest_path.db')

    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn, False

def init_db(db_path=None):
    """
    Initializes database tables according to specifications.
    Pre-seeds default student and administrator demo credentials.
    """
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        if is_pg:
            # PostgreSQL schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graphs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                    graph_name TEXT NOT NULL,
                    graph_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    shortest_path TEXT NOT NULL,
                    total_distance REAL,
                    execution_time REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            # SQLite schema
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

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_graphs_user_id ON graphs(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user_id ON search_history(user_id);")

        conn.commit()

        # Pre-seed demo users if not present
        if is_pg:
            cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (full_name, username, email, password_hash) VALUES (%s, %s, %s, %s)",
                    ("Admin User", "admin", "admin@college.edu", generate_password_hash("password123"))
                )
            cursor.execute("SELECT id FROM users WHERE username = %s", ("student",))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (full_name, username, email, password_hash) VALUES (%s, %s, %s, %s)",
                    ("Student Demo", "student", "student@college.edu", generate_password_hash("password123"))
                )
        else:
            cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (full_name, username, email, password_hash) VALUES (?, ?, ?, ?)",
                    ("Admin User", "admin", "admin@college.edu", generate_password_hash("password123"))
                )
            cursor.execute("SELECT id FROM users WHERE username = ?", ("student",))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (full_name, username, email, password_hash) VALUES (?, ?, ?, ?)",
                    ("Student Demo", "student", "student@college.edu", generate_password_hash("password123"))
                )

        conn.commit()
    finally:
        conn.close()

# ==========================================
# USER MANAGEMENT FUNCTIONS
# ==========================================

def create_user(full_name, username, email, password_hash, db_path=None):
    """Insert a new user. Returns user_id or raises IntegrityError."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    u_clean = username.strip().lower()
    e_clean = email.strip().lower()
    now = datetime.utcnow()

    try:
        if is_pg:
            cursor.execute("""
                INSERT INTO users (full_name, username, email, password_hash, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (full_name.strip(), u_clean, e_clean, password_hash, now))
            row = cursor.fetchone()
            user_id = row['id'] if isinstance(row, dict) else row[0]
        else:
            cursor.execute("""
                INSERT INTO users (full_name, username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?);
            """, (full_name.strip(), u_clean, e_clean, password_hash, now))
            user_id = cursor.lastrowid
        conn.commit()
        return user_id
    finally:
        conn.close()

def get_user_by_username(username, db_path=None):
    """Fetch user record by username (case-insensitive)."""
    if not username:
        return None
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    target = username.strip().lower()
    try:
        if is_pg:
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = %s", (target,))
        else:
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = ?", (target,))
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def get_user_by_email(email, db_path=None):
    """Fetch user record by email (case-insensitive)."""
    if not email:
        return None
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    target = email.strip().lower()
    try:
        if is_pg:
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = %s", (target,))
        else:
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (target,))
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def get_user_by_id(user_id, db_path=None):
    """Fetch user record by ID."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        if is_pg:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def reset_password_by_username_or_email(identifier, new_password_hash, db_path=None):
    """Update user password given either username or email."""
    if not identifier:
        return False
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    target = identifier.strip().lower()
    try:
        if is_pg:
            cursor.execute("""
                UPDATE users SET password_hash = %s
                WHERE LOWER(username) = %s OR LOWER(email) = %s
            """, (new_password_hash, target, target))
        else:
            cursor.execute("""
                UPDATE users SET password_hash = ?
                WHERE LOWER(username) = ? OR LOWER(email) = ?
            """, (new_password_hash, target, target))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()

# ==========================================
# GRAPH MANAGEMENT FUNCTIONS
# ==========================================

def save_graph(user_id, graph_name, graph_data_json, db_path=None):
    """Save or update a graph for a specific user."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    g_name = graph_name.strip()
    now = datetime.utcnow()

    try:
        if is_pg:
            cursor.execute("SELECT id FROM graphs WHERE user_id = %s AND graph_name = %s", (user_id, g_name))
            existing = cursor.fetchone()
            if existing:
                graph_id = existing['id'] if isinstance(existing, dict) else existing[0]
                cursor.execute("""
                    UPDATE graphs SET graph_data = %s, updated_at = %s
                    WHERE id = %s AND user_id = %s
                """, (graph_data_json, now, graph_id, user_id))
            else:
                cursor.execute("""
                    INSERT INTO graphs (user_id, graph_name, graph_data, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (user_id, g_name, graph_data_json, now, now))
                row = cursor.fetchone()
                graph_id = row['id'] if isinstance(row, dict) else row[0]
        else:
            cursor.execute("SELECT id FROM graphs WHERE user_id = ? AND graph_name = ?", (user_id, g_name))
            existing = cursor.fetchone()
            if existing:
                graph_id = existing['id']
                cursor.execute("""
                    UPDATE graphs SET graph_data = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                """, (graph_data_json, now, graph_id, user_id))
            else:
                cursor.execute("""
                    INSERT INTO graphs (user_id, graph_name, graph_data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, g_name, graph_data_json, now, now))
                graph_id = cursor.lastrowid

        conn.commit()
        return graph_id
    finally:
        conn.close()

def get_user_graphs(user_id, db_path=None):
    """Return all graphs saved by the user."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        if is_pg:
            cursor.execute("""
                SELECT id, graph_name, created_at, updated_at
                FROM graphs WHERE user_id = %s
                ORDER BY updated_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, graph_name, created_at, updated_at
                FROM graphs WHERE user_id = ?
                ORDER BY updated_at DESC
            """, (user_id,))
        graphs = cursor.fetchall()
        return [dict(g) for g in graphs]
    finally:
        conn.close()

def get_graph_by_id(graph_id, user_id, db_path=None):
    """Return specific graph by ID, ensuring it belongs to the user."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        if is_pg:
            cursor.execute("SELECT * FROM graphs WHERE id = %s AND user_id = %s", (graph_id, user_id))
        else:
            cursor.execute("SELECT * FROM graphs WHERE id = ? AND user_id = ?", (graph_id, user_id))
        graph = cursor.fetchone()
        return dict(graph) if graph else None
    finally:
        conn.close()

def delete_graph(graph_id, user_id, db_path=None):
    """Delete a user's graph."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        if is_pg:
            cursor.execute("DELETE FROM graphs WHERE id = %s AND user_id = %s", (graph_id, user_id))
        else:
            cursor.execute("DELETE FROM graphs WHERE id = ? AND user_id = ?", (graph_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()

# ==========================================
# SEARCH HISTORY FUNCTIONS
# ==========================================

def add_search_history(user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, db_path=None):
    """Record a path search result in history."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    now = datetime.utcnow()

    try:
        if is_pg:
            cursor.execute("""
                INSERT INTO search_history (user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, now))
            row = cursor.fetchone()
            history_id = row['id'] if isinstance(row, dict) else row[0]
        else:
            cursor.execute("""
                INSERT INTO search_history (user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, source, destination, algorithm, shortest_path, total_distance, execution_time, now))
            history_id = cursor.lastrowid
        conn.commit()
        return history_id
    finally:
        conn.close()

def get_user_search_history(user_id, limit=100, db_path=None):
    """Fetch search history for a user, sorted descending by created_at."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        if is_pg:
            cursor.execute("""
                SELECT id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at
                FROM search_history WHERE user_id = %s
                ORDER BY created_at DESC LIMIT %s
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at
                FROM search_history WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, limit))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def clear_user_search_history(user_id, db_path=None):
    """Clear all search history for a user."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        if is_pg:
            cursor.execute("DELETE FROM search_history WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected
    finally:
        conn.close()

def get_user_history_stats(user_id, db_path=None):
    """Retrieve statistical summary for dashboard."""
    conn, is_pg = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        if is_pg:
            cursor.execute("SELECT COUNT(*) as count FROM search_history WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            total_searches = row['count'] if isinstance(row, dict) else row[0]

            cursor.execute("""
                SELECT algorithm, COUNT(*) as count
                FROM search_history WHERE user_id = %s
                GROUP BY algorithm
            """, (user_id,))
            algorithm_counts = {
                (r['algorithm'] if isinstance(r, dict) else r[0]): (r['count'] if isinstance(r, dict) else r[1])
                for r in cursor.fetchall()
            }

            cursor.execute("""
                SELECT id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at
                FROM search_history WHERE user_id = %s
                ORDER BY created_at DESC LIMIT 5
            """, (user_id,))
            recent = [dict(r) for r in cursor.fetchall()]
        else:
            cursor.execute("SELECT COUNT(*) as count FROM search_history WHERE user_id = ?", (user_id,))
            total_searches = cursor.fetchone()['count']

            cursor.execute("""
                SELECT algorithm, COUNT(*) as count
                FROM search_history WHERE user_id = ?
                GROUP BY algorithm
            """, (user_id,))
            algorithm_counts = {row['algorithm']: row['count'] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT id, source, destination, algorithm, shortest_path, total_distance, execution_time, created_at
                FROM search_history WHERE user_id = ?
                ORDER BY created_at DESC LIMIT 5
            """, (user_id,))
            recent = [dict(r) for r in cursor.fetchall()]

        return {
            "total_searches": total_searches,
            "algorithm_counts": algorithm_counts,
            "recent_searches": recent
        }
    finally:
        conn.close()
