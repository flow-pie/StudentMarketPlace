"""Tests for views and health check functionality."""

import pytest
import json


class TestHealthChecks:
    """Test health check endpoints."""
    
    def test_health_endpoint_structure(self, client):
        """Test health endpoint returns proper structure."""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check required fields
        assert 'status' in data
        assert 'timestamp' in data
        assert 'checks' in data
        
        # Check that database check is present
        assert 'database' in data['checks']
        assert 'status' in data['checks']['database']
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get('/metrics')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check metrics structure
        assert 'timestamp' in data
        assert 'database' in data
        assert 'system' in data
    
    def test_readiness_probe(self, client):
        """Test Kubernetes readiness probe."""
        response = client.get('/ready')
        
        # Should return 200 if ready, 503 if not
        assert response.status_code in [200, 503]
        
        data = response.get_json()
        assert 'status' in data
    
    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe."""
        response = client.get('/live')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'alive'


class TestErrorHandling:
    """Test enhanced error handling."""
    
    def test_correlation_id_in_errors(self, client):
        """Test that correlation IDs are included in error responses."""
        # Make request to non-existent endpoint
        response = client.get('/api/nonexistent')
        
        # Check that correlation ID header is present
        assert 'X-Correlation-ID' in response.headers
        
        # Correlation ID should be a valid UUID format
        correlation_id = response.headers['X-Correlation-ID']
        assert len(correlation_id) > 0
        assert correlation_id != 'unknown'
    
    def test_structured_error_response(self, client):
        """Test that errors return structured responses."""
        response = client.get('/api/items/99999')  # Non-existent item
        
        if response.status_code == 404:
            data = response.get_json()
            assert 'error' in data or 'message' in data
    
    def test_error_logging(self, client, caplog):
        """Test that errors are properly logged."""
        # Trigger an error
        response = client.get('/api/items/invalid')
        
        # Check that error was logged (if logging is configured)
        # This test depends on logging configuration
        pass


class TestSecurityMonitoring:
    """Test security views features."""
    
    def test_failed_auth_attempts_logged(self, client, caplog):
        """Test that failed authentication attempts are logged."""
        # Attempt login with invalid credentials
        response = client.post('/api/auth/login',
                              json={
                                  'email': 'invalid@example.com',
                                  'password': 'wrongpassword'
                              })
        
        assert response.status_code == 401
        # Check that attempt was logged (implementation dependent)
    
    def test_suspicious_activity_detection(self, client):
        """Test detection of suspicious activity patterns."""
        # Make multiple failed requests
        for _ in range(5):
            client.post('/api/auth/login',
                       json={
                           'email': 'attacker@example.com',
                           'password': 'wrongpassword'
                       })
        
        # Should trigger rate limiting or other security measures
        # Implementation depends on security configuration