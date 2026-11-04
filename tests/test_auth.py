import pytest
import os
import tempfile
from app import app
from database.database import init_db

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-12345'
    os.environ['DATABASE_PATH'] = db_path

    with app.app_context():
        init_db(db_path)

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)

def test_register_success(client):
    response = client.post('/register', data={
        'full_name': 'Alice Smith',
        'username': 'alicesmith',
        'email': 'alice@college.edu',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome to Shortest Path Finder" in response.data or b"Dashboard" in response.data

def test_register_duplicate_username(client):
    client.post('/register', data={
        'full_name': 'Alice Smith',
        'username': 'aliceuser',
        'email': 'alice1@college.edu',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    client.get('/logout')
    response = client.post('/register', data={
        'full_name': 'Another Alice',
        'username': 'aliceuser',
        'email': 'alice2@college.edu',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert b"Username is already registered" in response.data

def test_login_success(client):
    # Register first
    client.post('/register', data={
        'full_name': 'Bob Jones',
        'username': 'bobjones',
        'email': 'bob@college.edu',
        'password': 'secretpassword',
        'confirm_password': 'secretpassword'
    })
    # Logout
    client.get('/logout')
    # Login with username
    response = client.post('/login', data={
        'username': 'bobjones',
        'password': 'secretpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back, Bob Jones" in response.data

def test_login_with_email(client):
    client.post('/register', data={
        'full_name': 'Charlie Brown',
        'username': 'charlieb',
        'email': 'charlie@college.edu',
        'password': 'mypassword123',
        'confirm_password': 'mypassword123'
    })
    client.get('/logout')
    response = client.post('/login', data={
        'username': 'charlie@college.edu',
        'password': 'mypassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back, Charlie Brown" in response.data

def test_login_invalid_password(client):
    client.post('/register', data={
        'full_name': 'Dave Miller',
        'username': 'davemiller',
        'email': 'dave@college.edu',
        'password': 'correctpassword',
        'confirm_password': 'correctpassword'
    })
    client.get('/logout')
    response = client.post('/login', data={
        'username': 'davemiller',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b"Invalid username/email or password" in response.data

def test_protected_routes_redirect_unauthenticated(client):
    # Without login, accessing dashboard should redirect to login
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    # API routes should return 401
    api_response = client.get('/api/graphs')
    assert api_response.status_code == 401
    assert api_response.get_json()['success'] is False

def test_forgot_password_reset(client):
    client.post('/register', data={
        'full_name': 'Eve Adams',
        'username': 'eveadams',
        'email': 'eve@college.edu',
        'password': 'oldpassword',
        'confirm_password': 'oldpassword'
    })
    client.get('/logout')

    # Reset password
    reset_resp = client.post('/forgot-password', data={
        'identifier': 'eveadams',
        'new_password': 'newpassword123',
        'confirm_password': 'newpassword123'
    }, follow_redirects=True)
    assert b"Password updated successfully" in reset_resp.data

    # Verify login with new password
    login_resp = client.post('/login', data={
        'username': 'eveadams',
        'password': 'newpassword123'
    }, follow_redirects=True)
    assert b"Welcome back, Eve Adams" in login_resp.data

def test_malformed_url_redirects_to_login(client):
    # Malformed concatenated domain from old browser history/tab
    resp = client.get('/https:/shortest-path-sooty.vercel.app/', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'] == '/login'

def test_unknown_path_redirects_gracefully(client):
    # Unknown 404 route should redirect safely to login when unauthenticated
    resp = client.get('/some-nonexistent-route', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'] == '/login'
