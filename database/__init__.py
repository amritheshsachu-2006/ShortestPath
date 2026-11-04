# Database package initialization
from .database import (
    init_db,
    get_db_connection,
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    reset_password_by_username_or_email,
    save_graph,
    get_user_graphs,
    get_graph_by_id,
    delete_graph,
    add_search_history,
    get_user_search_history,
    clear_user_search_history,
    get_user_history_stats
)

