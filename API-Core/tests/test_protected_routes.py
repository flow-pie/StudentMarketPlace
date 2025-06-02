import pytest
from flask import current_app
from flask_jwt_extended import create_access_token

import jwt
from app.models.user import User

def test_token_validity(test_user, app):
    with app.app_context():
        # Convert user_id to string for JWT identity
        token = create_access_token(identity=str(test_user.user_id))
        decoded = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        assert decoded['sub'] == str(test_user.user_id)

def test_protected_route_access(client, test_user, auth_headers):
    """Test successful access to protected route"""
    headers = {
        'Authorization': auth_headers['Authorization'],
    }
    response = client.get(
        '/api/items/protected',
        headers=headers
    )
    assert response.status_code == 200

def test_unprotected_route(client):
    """Verify unprotected routes still work"""
    response = client.get('/api/items/public')
    assert response.status_code == 200

def test_admin_route_non_admin(client, test_user, auth_headers):
    """Test admin route with non-admin user"""
    response = client.get(
        '/api/items/admin',
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "Admin access required" in response.json['error']

def test_expired_token(client, expired_token):
    """Test token expiration handling"""
    response = client.get(
        '/api/items/protected',
        headers={'Authorization': f'Bearer {expired_token}'}
    )
    assert response.status_code == 401
    assert response.json['error'] == "Expired token"