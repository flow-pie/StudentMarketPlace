import pytest

from app import db
from app.models import User


def test_password_hashing():
    u = User()
    u.set_password('secure123')
    assert u.password_hash is not None
    assert u.password_hash != 'secure123'
    assert u.check_password('secure123') is True
    assert u.check_password('wrong') is False


def test_registration(client, db_fixture):
    # Verify table exists
    with client.application.app_context():
        inspector = db.inspect(db_fixture.engine)
        assert 'users' in inspector.get_table_names()

    # Test registration
    test_data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "first_name": "Test",
        "last_name": "User"
    }

    response = client.post('/api/auth/register', json=test_data)

    if response.status_code != 201:
        print("ERROR RESPONSE:", response.json)

    assert response.status_code == 201
    assert response.json['message'] == 'Registration successful'

def test_duplicate_email(client, db_fixture):
    client.post('/api/auth/register', json={
        "email": "dupe@example.com",
        "password": "pass123",
        "first_name": "First",
        "last_name": "User"
    })

    response = client.post('/api/auth/register', json={
        "email": "dupe@example.com",
        "password": "pass123",
        "first_name": "Second",
        "last_name": "User"
    })

    if response.status_code != 400:
        print("ERROR RESPONSE:", response.json)

    assert response.status_code == 400
    assert "Email already registered" in str(response.data)


def test_successful_login(client, test_user):
    response = client.post('/api/auth/login', json={
        "email": test_user.email,
        "password": "testpassword123"
    })

    assert response.status_code == 200
    assert 'access_token' in response.json


def test_invalid_password(client, test_user):
    response = client.post('/api/auth/login', json={
        "email": test_user.email,
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert "Invalid credentials" in response.json['error']


def test_inactive_user(client, inactive_user):
    response = client.post('/api/auth/login', json={
        "email": inactive_user.email,
        "password": "testpassword123"
    })

    assert response.status_code == 403
    assert "Account not active" in response.json['error']