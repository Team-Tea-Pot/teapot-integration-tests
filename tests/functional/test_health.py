"""
Functional tests for health check endpoint.
"""

import pytest
import requests
from datetime import datetime


@pytest.mark.functional
@pytest.mark.health
@pytest.mark.smoke
class TestHealthEndpoint:
    """Test suite for /health endpoint."""
    
    def test_health_check_returns_200(self, api_client: requests.Session, config: dict):
        """Test that health check endpoint returns 200 OK."""
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_health_check_response_structure(self, api_client: requests.Session, config: dict):
        """Test that health check returns correct JSON structure."""
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "status" in data, "Response missing 'status' field"
        assert "timestamp" in data, "Response missing 'timestamp' field"
        assert "version" in data, "Response missing 'version' field"
    
    def test_health_check_status_value(self, api_client: requests.Session, config: dict):
        """Test that health check returns 'healthy' status."""
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy", f"Expected status 'healthy', got '{data['status']}'"
    
    def test_health_check_timestamp_format(self, api_client: requests.Session, config: dict):
        """Test that health check timestamp is in correct ISO format."""
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify timestamp can be parsed as ISO 8601
        try:
            timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
            assert timestamp is not None
        except (ValueError, KeyError) as e:
            pytest.fail(f"Invalid timestamp format: {e}")
    
    def test_health_check_version_format(self, api_client: requests.Session, config: dict):
        """Test that health check returns valid version string."""
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        version = data.get("version", "")
        assert isinstance(version, str), "Version should be a string"
        assert len(version) > 0, "Version should not be empty"
    
    def test_health_check_no_auth_required(self, api_client: requests.Session, config: dict):
        """Test that health check doesn't require authentication."""
        # Remove any existing auth headers
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        
        response = session.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200, "Health check should not require authentication"
    
    def test_health_check_response_time(self, api_client: requests.Session, config: dict):
        """Test that health check responds quickly (< 1 second)."""
        import time
        
        start_time = time.time()
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 1.0, f"Health check took {elapsed_time:.2f}s, expected < 1s"
    
    def test_health_check_content_type(self, api_client: requests.Session, config: dict):
        """Test that health check returns JSON content type."""
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type.lower(), \
            f"Expected JSON content type, got '{content_type}'"
