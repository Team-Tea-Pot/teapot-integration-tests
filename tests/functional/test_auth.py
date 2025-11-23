"""
Functional tests for authentication endpoints.
Tests /auth/login and /auth/register endpoints.
"""

import pytest
import requests
import re


@pytest.mark.functional
@pytest.mark.auth
class TestAuthLogin:
    """Test suite for /auth/login endpoint."""
    
    def test_login_with_valid_credentials(self, api_client: requests.Session, config: dict):
        """Test successful login with valid email and password."""
        # First register a user
        unique_email = f"login_test_{config['test_user']['username']}@teapot.lk"
        register_data = {
            "email": unique_email,
            "password": "ValidPass123!",
            "confirmPassword": "ValidPass123!",
            "username": f"loginuser_{config['test_user']['username']}",
            "tp": "+94771234999"
        }
        
        api_client.post(
            f"{config['base_url']}/auth/register",
            json=register_data,
            timeout=config["timeout"]
        )
        
        # Now login
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={
                "email": unique_email,
                "password": "ValidPass123!"
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "token" in data, "Response missing 'token' field"
        assert "user" in data, "Response missing 'user' field"
        assert isinstance(data["token"], str), "Token should be a string"
        assert len(data["token"]) > 0, "Token should not be empty"
    
    def test_login_response_structure(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str):
        """Test that login returns correct response structure."""
        password = "TestPass123!"
        
        # Register
        api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "confirmPassword": password,
                "username": unique_username,
                "tp": "+94771234888"
            },
            timeout=config["timeout"]
        )
        
        # Login
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={"email": unique_email, "password": password},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify user object structure
        user = data["user"]
        assert "id" in user, "User object missing 'id'"
        assert "email" in user, "User object missing 'email'"
        assert "username" in user, "User object missing 'username'"
        assert user["email"] == unique_email
    
    def test_login_with_invalid_email(self, api_client: requests.Session, config: dict):
        """Test login fails with non-existent email."""
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={
                "email": "nonexistent@teapot.lk",
                "password": "AnyPass123!"
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_login_with_wrong_password(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str):
        """Test login fails with incorrect password."""
        correct_password = "CorrectPass123!"
        
        # Register user
        api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": correct_password,
                "confirmPassword": correct_password,
                "username": unique_username,
                "tp": "+94771234777"
            },
            timeout=config["timeout"]
        )
        
        # Try login with wrong password
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={
                "email": unique_email,
                "password": "WrongPass123!"
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_login_with_missing_email(self, api_client: requests.Session, config: dict):
        """Test login fails when email is missing."""
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={"password": "SomePass123!"},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_login_with_missing_password(self, api_client: requests.Session, config: dict):
        """Test login fails when password is missing."""
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={"email": "test@teapot.lk"},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_login_with_invalid_email_format(self, api_client: requests.Session, config: dict):
        """Test login fails with malformed email."""
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={
                "email": "not-an-email",
                "password": "SomePass123!"
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code in [400, 401], f"Expected 400 or 401, got {response.status_code}"
    
    def test_login_error_response_structure(self, api_client: requests.Session, config: dict):
        """Test that error responses have correct structure."""
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={
                "email": "invalid@teapot.lk",
                "password": "Wrong123!"
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401
        data = response.json()
        
        assert "error" in data, "Error response missing 'error' field"
        assert "message" in data, "Error response missing 'message' field"
        assert "timestamp" in data, "Error response missing 'timestamp' field"


@pytest.mark.functional
@pytest.mark.auth
class TestAuthRegister:
    """Test suite for /auth/register endpoint."""
    
    def test_register_with_valid_data(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test successful registration with valid data."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": "StrongPass123!",
                "confirmPassword": "StrongPass123!",
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "token" in data, "Response missing 'token' field"
        assert "user" in data, "Response missing 'user' field"
    
    def test_register_returns_jwt_token(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test that registration returns a valid JWT token."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201
        data = response.json()
        
        token = data["token"]
        # JWT format: header.payload.signature
        assert token.count('.') == 2, "Token should be in JWT format (3 parts separated by dots)"
    
    def test_register_with_weak_password(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test registration fails with weak password (no special char)."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": "weakpass123",
                "confirmPassword": "weakpass123",
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_register_with_short_password(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test registration fails with password shorter than 8 characters."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": "Short1!",
                "confirmPassword": "Short1!",
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_register_with_mismatched_passwords(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test registration fails when passwords don't match."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": "Password123!",
                "confirmPassword": "Different123!",
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_register_with_invalid_email_format(self, api_client: requests.Session, config: dict, unique_username: str, unique_phone: str):
        """Test registration fails with invalid email format."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": "not-valid-email",
                "password": "ValidPass123!",
                "confirmPassword": "ValidPass123!",
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_register_with_duplicate_email(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test registration fails with already registered email."""
        register_data = {
            "email": unique_email,
            "password": "ValidPass123!",
            "confirmPassword": "ValidPass123!",
            "username": unique_username,
            "tp": unique_phone
        }
        
        # First registration
        response1 = api_client.post(
            f"{config['base_url']}/auth/register",
            json=register_data,
            timeout=config["timeout"]
        )
        assert response1.status_code == 201
        
        # Second registration with same email
        register_data["username"] = f"{unique_username}_2"
        response2 = api_client.post(
            f"{config['base_url']}/auth/register",
            json=register_data,
            timeout=config["timeout"]
        )
        
        assert response2.status_code == 409, f"Expected 409, got {response2.status_code}"
    
    def test_register_with_invalid_phone_format(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str):
        """Test registration fails with invalid phone number format."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": "ValidPass123!",
                "confirmPassword": "ValidPass123!",
                "username": unique_username,
                "tp": "123"  # Invalid phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_register_with_invalid_username(self, api_client: requests.Session, config: dict, unique_email: str, unique_phone: str):
        """Test registration fails with invalid username (too short)."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": "ValidPass123!",
                "confirmPassword": "ValidPass123!",
                "username": "ab",  # Too short (< 3 chars)
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_register_with_username_special_chars(self, api_client: requests.Session, config: dict, unique_email: str, unique_phone: str):
        """Test registration fails with invalid characters in username."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": "ValidPass123!",
                "confirmPassword": "ValidPass123!",
                "username": "user@name!",  # Invalid characters
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_register_with_missing_required_fields(self, api_client: requests.Session, config: dict):
        """Test registration fails when required fields are missing."""
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": "test@teapot.lk"
                # Missing password, username, tp
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
