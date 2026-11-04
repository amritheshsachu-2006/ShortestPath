import os
import json
import functools
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import timedelta

from config import Config
from database.database import (
    init_db,
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
from utils.graph_utils import (
    parse_cytoscape_graph,
    validate_graph_payload,
    get_sample_graphs,
    generate_random_graph
)
from algorithms import (
    run_algorithm,
    compare_all_algorithms,
    ALGORITHMS
)

# Absolute paths for Vercel Serverless container compatibility
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(base_dir, 'templates'),
    static_folder=os.path.join(base_dir, 'static')
)
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(days=7)

# Safe database initialization
try:
    with app.app_context():
        init_db()
except Exception as e:
    print(f"[Startup Warning] Database initialization deferred: {e}")

# WSGI Middleware to fix Vercel Serverless Function routing and malformed URLs
class VercelPathFixMiddleware:
    """Restores the original request URI if rewritten by Vercel serverless functions
    and intercepts malformed concatenated URLs.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO', '')
        orig_uri = environ.get('HTTP_X_FORWARDED_URI') or environ.get('RAW_URI') or environ.get('REQUEST_URI') or ''

        # Intercept malformed recursive URLs like /https:/shortest-path-sooty.vercel.app/
        if 'http:/' in path_info or 'https:/' in path_info or 'vercel.app' in path_info or 'http:/' in orig_uri or 'https:/' in orig_uri or 'vercel.app' in orig_uri:
            start_response('302 Found', [('Location', '/login'), ('Content-Length', '0')])
            return [b'']

        if orig_uri:
            clean_orig = orig_uri.split('?')[0]
            if clean_orig and clean_orig not in ('/api/index', '/api/index/'):
                environ['PATH_INFO'] = clean_orig

        curr_path = environ.get('PATH_INFO', '')
        if curr_path in ('/api/index', '/api/index/'):
            environ['PATH_INFO'] = '/'
        elif curr_path.startswith('/api/index/'):
            environ['PATH_INFO'] = curr_path[len('/api/index'):]

        return self.wsgi_app(environ, start_response)

# Apply proxy headers first, then URL path normalization
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)

def login_required(view):
    """Decorator to require login for web pages and JSON APIs."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "error": "Authentication required. Please log in."}), 401
            flash("Please log in to access this page.", "warning")
            clean_path = request.path if request.path and request.path not in ('/', '/login', '/logout') and 'http' not in request.path else None
            if clean_path:
                return redirect(url_for('login', next=clean_path))
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.context_processor
def inject_user():
    """Make user info available across all Jinja templates."""
    if 'user_id' in session:
        return {
            'current_user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'full_name': session.get('full_name')
            }
        }
    return {'current_user': None}

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('login.html', identifier=identifier)

        # Allow login via username or email
        user = get_user_by_username(identifier)
        if not user:
            user = get_user_by_email(identifier)

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            if remember:
                session.permanent = True
            
            flash(f"Welcome back, {user['full_name']}!", "success")
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//') and not next_page.startswith('/api/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username/email or password. Please try again.", "danger")
            return render_template('login.html', identifier=identifier)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not full_name or not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html', full_name=full_name, username=username, email=email)

        if len(username) < 3 or not username.isalnum():
            flash("Username must be at least 3 characters and contain only letters and numbers.", "danger")
            return render_template('register.html', full_name=full_name, username=username, email=email)

        if '@' not in email or '.' not in email:
            flash("Please enter a valid email address.", "danger")
            return render_template('register.html', full_name=full_name, username=username, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html', full_name=full_name, username=username, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html', full_name=full_name, username=username, email=email)

        if get_user_by_username(username):
            flash("Username is already registered. Please choose another or log in.", "danger")
            return render_template('register.html', full_name=full_name, username=username, email=email)

        if get_user_by_email(email):
            flash("Email address is already registered. Please log in.", "danger")
            return render_template('register.html', full_name=full_name, username=username, email=email)

        password_hash = generate_password_hash(password)
        try:
            user_id = create_user(full_name, username, email, password_hash)
            session.clear()
            session['user_id'] = user_id
            session['username'] = username
            session['full_name'] = full_name
            flash("Account created successfully! Welcome to Shortest Path Finder.", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"An error occurred during registration: {str(e)}", "danger")
            return render_template('register.html', full_name=full_name, username=username, email=email)

    return render_template('register.html')

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Secure local development reset flow."""
    identifier = request.form.get('identifier', '').strip()
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not identifier or not new_password:
        flash("Identifier and new password are required.", "danger")
        return redirect(url_for('login'))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters.", "danger")
        return redirect(url_for('login'))

    if new_password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for('login'))

    user = get_user_by_username(identifier) or get_user_by_email(identifier)
    if not user:
        flash("No account found matching that username or email.", "danger")
        return redirect(url_for('login'))

    new_hash = generate_password_hash(new_password)
    reset_password_by_username_or_email(identifier, new_hash)
    flash("Password updated successfully! Please log in with your new password.", "success")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

# ==========================================
# MAIN APPLICATION PAGES
# ==========================================

@app.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/api/index')
def api_index_route():
    """Fallback route for Vercel serverless function."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    stats = get_user_history_stats(user_id)
    saved_graphs = get_user_graphs(user_id)
    return render_template('dashboard.html', stats=stats, saved_graphs=saved_graphs, sample_graphs=get_sample_graphs())

@app.route('/editor')
@login_required
def graph_editor():
    return render_template('graph_editor.html', sample_graphs=get_sample_graphs())

@app.route('/finder')
@login_required
def shortest_path():
    return render_template('shortest_path.html', algorithms=ALGORITHMS, sample_graphs=get_sample_graphs())

@app.route('/visualization')
@login_required
def visualization():
    return render_template('visualization.html', algorithms=ALGORITHMS, sample_graphs=get_sample_graphs())

@app.route('/comparison')
@login_required
def comparison():
    return render_template('comparison.html', algorithms=ALGORITHMS, sample_graphs=get_sample_graphs())

@app.route('/history')
@login_required
def history():
    user_id = session['user_id']
    history_items = get_user_search_history(user_id, limit=100)
    return render_template('history.html', history=history_items)

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.route('/api/stats', methods=['GET'])
@login_required
def api_stats():
    user_id = session['user_id']
    stats = get_user_history_stats(user_id)
    graphs = get_user_graphs(user_id)
    return jsonify({
        "success": True,
        "stats": stats,
        "saved_graphs_count": len(graphs)
    })

@app.route('/api/samples', methods=['GET'])
@login_required
def api_samples():
    return jsonify({"success": True, "samples": get_sample_graphs()})

@app.route('/api/samples/<key>', methods=['GET'])
@login_required
def api_sample_detail(key):
    samples = get_sample_graphs()
    if key in samples:
        return jsonify({"success": True, "graph": samples[key]})
    return jsonify({"success": False, "error": f"Sample '{key}' not found."}), 404

@app.route('/api/random-graph', methods=['POST'])
@login_required
def api_random_graph():
    data = request.get_json() or {}
    num_nodes = int(data.get('num_nodes', 6))
    density = float(data.get('density', 0.4))
    directed = bool(data.get('directed', True))
    allow_negative = bool(data.get('allow_negative', False))
    graph = generate_random_graph(num_nodes, density, directed, allow_negative)
    return jsonify({"success": True, "graph": graph})

@app.route('/api/graphs', methods=['GET', 'POST'])
@login_required
def api_user_graphs():
    user_id = session['user_id']
    if request.method == 'GET':
        graphs = get_user_graphs(user_id)
        return jsonify({"success": True, "graphs": graphs})

    data = request.get_json() or {}
    graph_name = data.get('graph_name', '').strip()
    graph_data = data.get('graph_data')

    if not graph_name:
        return jsonify({"success": False, "error": "Graph name is required."}), 400
    if not graph_data:
        return jsonify({"success": False, "error": "Graph data is required."}), 400

    graph_data_json = json.dumps(graph_data) if not isinstance(graph_data, str) else graph_data
    graph_id = save_graph(user_id, graph_name, graph_data_json)
    return jsonify({"success": True, "graph_id": graph_id, "message": f"Graph '{graph_name}' saved successfully."})

@app.route('/api/graphs/<int:graph_id>', methods=['GET', 'DELETE'])
@login_required
def api_graph_item(graph_id):
    user_id = session['user_id']
    if request.method == 'GET':
        g = get_graph_by_id(graph_id, user_id)
        if not g:
            return jsonify({"success": False, "error": "Graph not found."}), 404
        g_data = json.loads(g['graph_data']) if isinstance(g['graph_data'], str) else g['graph_data']
        return jsonify({"success": True, "graph": g, "elements": g_data})

    deleted = delete_graph(graph_id, user_id)
    if deleted:
        return jsonify({"success": True, "message": "Graph deleted successfully."})
    return jsonify({"success": False, "error": "Graph not found or could not be deleted."}), 404

@app.route('/api/algorithm/run', methods=['POST'])
@login_required
def api_run_algorithm():
    user_id = session['user_id']
    data = request.get_json() or {}

    algo_key = data.get('algorithm')
    source = data.get('source')
    destination = data.get('destination')
    graph_data = data.get('graph_data')
    save_to_history = data.get('save_to_history', True)

    if not algo_key:
        return jsonify({"success": False, "error": "Algorithm is required."}), 400

    directed = data.get('directed', True)
    vertices, edges, adj, is_dir = parse_cytoscape_graph(graph_data, directed=directed)

    valid, err_msg = validate_graph_payload(vertices, edges, source=source, destination=destination)
    if not valid:
        return jsonify({"success": False, "error": err_msg}), 400

    result = run_algorithm(algo_key, vertices, edges, adj, source, destination)

    # Save to history if valid result and requested
    if save_to_history and result.get("success"):
        path_str = " → ".join(result.get("path", [])) if result.get("path") else "No path"
        dist_val = result.get("total_distance")
        exec_time = result.get("execution_time_ms", 0.0)
        algo_display = ALGORITHMS.get(algo_key.lower(), {}).get("name", algo_key)

        add_search_history(
            user_id=user_id,
            source=source,
            destination=destination,
            algorithm=algo_display,
            shortest_path=path_str,
            total_distance=dist_val,
            execution_time=exec_time
        )

    return jsonify(result)

@app.route('/api/algorithm/compare', methods=['POST'])
@login_required
def api_compare_algorithms():
    data = request.get_json() or {}
    source = data.get('source')
    destination = data.get('destination')
    graph_data = data.get('graph_data')
    directed = data.get('directed', True)

    vertices, edges, adj, is_dir = parse_cytoscape_graph(graph_data, directed=directed)
    valid, err_msg = validate_graph_payload(vertices, edges, source=source, destination=destination)
    if not valid:
        return jsonify({"success": False, "error": err_msg}), 400

    comparison_results = compare_all_algorithms(vertices, edges, adj, source, destination)
    return jsonify({
        "success": True,
        "source": source,
        "destination": destination,
        "num_vertices": len(vertices),
        "num_edges": len(edges),
        "results": comparison_results
    })

@app.route('/api/history', methods=['GET', 'DELETE'])
@login_required
def api_history():
    user_id = session['user_id']
    if request.method == 'GET':
        history_items = get_user_search_history(user_id, limit=100)
        return jsonify({"success": True, "history": history_items})

    affected = clear_user_search_history(user_id)
    return jsonify({"success": True, "message": f"Cleared {affected} history records."})

# ==========================================
# ERROR HANDLERS (Safe Serverless Fallbacks)
# ==========================================

@app.errorhandler(404)
def handle_404(e):
    """Graceful 404 handler preventing dead-ends or broken URL loops."""
    raw = request.path or ''
    if 'http' in raw or 'vercel.app' in raw or raw.startswith('//'):
        return redirect(url_for('login'))
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.errorhandler(500)
def handle_500(e):
    """Graceful 500 handler."""
    return render_template('login.html', error="An unexpected server error occurred. Please try logging in again."), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
