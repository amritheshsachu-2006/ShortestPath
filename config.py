import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aga-shortest-path-secret-key-2026-academic-secure')
    DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'shortest_path.db'))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max payload

