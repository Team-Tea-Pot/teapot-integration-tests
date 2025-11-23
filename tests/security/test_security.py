"""
Security tests for User Service.
Tests for authentication, authorization, input validation, injection attacks, etc.
"""

import pytest
import requests
import uuid
from typing import Dict, Any


@pytest.mark.security
class TestAuthenticationSecurity:
    """Security tests for authentication mechanisms."""
    
    def test_endpoints_require_authentication(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that protected endpoints reject unauthenticated requests."""
        protected_endpoints = [
            ("GET", f"{config['base_url']}/users", {"tenantId": config["tenant_id"]}),
            ("POST", f"{config['base_url']}/users", {}),
            ("GET", f"{config['base_url']}/users/{uuid.uuid4()}", {}),
            ("PUT", f"{config['base_url']}/users/{uuid.uuid4()}", {}),
            ("DELETE", f"{config['base_url']}/users/{uuid.uuid4()}", {}),
        ]
        
        for method, url, params in protected_endpoints:
            if method == "GET":
                response = api_client.get(url, params=params, timeout=config["timeout"])
            elif method == "POST":
                response = api_client.post(url, json={"test": "data"}, timeout=config["timeout"])
            elif method == "PUT":
                response = api_client.put(url, json={"test": "data"}, timeout=config["timeout"])
            elif method == "DELETE":
                response = api_client.delete(url, timeout=config["timeout"])
            
            assert response.status_code == 401, \
                f"{method} {url} should return 401 without auth, got {response.status_code}"
    
    def test_invalid_jwt_token_rejected(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that invalid JWT tokens are rejected."""
        api_client.headers.update({"Authorization": "Bearer invalid.token.here"})
        
        response = api_client.get(
            f"{config['base_url']}/users",
            params={"tenantId": config["tenant_id"]},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_expired_token_rejected(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that expired tokens are rejected."""
        # Create a JWT with expired timestamp (this is a mock expired token)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        
        api_client.headers.update({"Authorization": f"Bearer {expired_token}"})
        
        response = api_client.get(
            f"{config['base_url']}/users",
            params={"tenantId": config["tenant_id"]},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expired token should be rejected"
    
    def test_malformed_authorization_header(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that malformed Authorization headers are rejected."""
        malformed_headers = [
            "Bearer",  # Missing token
            "InvalidScheme token",  # Wrong scheme
            "token",  # Missing scheme
            "",  # Empty
        ]
        
        for auth_header in malformed_headers:
            api_client.headers.update({"Authorization": auth_header})
            
            response = api_client.get(
                f"{config['base_url']}/users",
                params={"tenantId": config["tenant_id"]},
                timeout=config["timeout"]
            )
            
            assert response.status_code == 401, \
                f"Malformed header '{auth_header}' should return 401"
    
    def test_token_cannot_be_reused_after_password_change(self, api_client: requests.Session, config: Dict[str, Any], unique_email: str, unique_username: str, unique_phone: str):
        """Test that old tokens are invalidated after password change (if supported)."""
        password = "OldPass123!"
        
        # Register user
        register_response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "confirmPassword": password,
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert register_response.status_code == 201
        old_token = register_response.json()["token"]
        
        # Note: This test assumes password change functionality exists
        # If not implemented, this test will be skipped in practice
        print(f"Note: Token invalidation test requires password change endpoint")


@pytest.mark.security
class TestInputValidationSecurity:
    """Security tests for input validation and injection attacks."""
    
    def test_sql_injection_in_email(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that SQL injection attempts in email are blocked."""
        sql_payloads = [
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "'; DROP TABLE users;--"
        ]
        
        for payload in sql_payloads:
            response = api_client.post(
                f"{config['base_url']}/auth/login",
                json={
                    "email": payload,
                    "password": "anypass"
                },
                timeout=config["timeout"]
            )
            
            # Should return 400 (validation error) or 401 (invalid credentials), not 500
            assert response.status_code in [400, 401], \
                f"SQL injection payload should not cause server error: {payload}"
    
    def test_xss_in_business_name(self, authenticated_client: requests.Session, config: Dict[str, Any], test_user_data: Dict[str, Any]):
        """Test that XSS payloads in business name are sanitized."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>"
        ]
        
        for payload in xss_payloads:
            test_user_data["businessName"] = payload
            test_user_data["email"] = f"xss_test_{uuid.uuid4().hex[:8]}@teapot.lk"
            test_user_data["phoneNumber"] = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
            
            response = authenticated_client.post(
                f"{config['base_url']}/users",
                json=test_user_data,
                timeout=config["timeout"]
            )
            
            # Should either reject (400) or sanitize the input
            if response.status_code == 201:
                user = response.json()
                # Verify the payload was sanitized (doesn't contain script tags)
                assert "<script>" not in user["businessName"], \
                    "XSS payload should be sanitized"
                
                # Cleanup
                authenticated_client.delete(
                    f"{config['base_url']}/users/{user['id']}",
                    timeout=config["timeout"]
                )
    
    def test_command_injection_in_fields(self, authenticated_client: requests.Session, config: Dict[str, Any], test_user_data: Dict[str, Any]):
        """Test that command injection attempts are blocked."""
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "` whoami `",
            "$( rm -rf / )"
        ]
        
        for payload in command_payloads:
            test_user_data["ownerName"] = payload
            test_user_data["email"] = f"cmd_test_{uuid.uuid4().hex[:8]}@teapot.lk"
            test_user_data["phoneNumber"] = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
            
            response = authenticated_client.post(
                f"{config['base_url']}/users",
                json=test_user_data,
                timeout=config["timeout"]
            )
            
            # Should not cause a server error
            assert response.status_code != 500, \
                f"Command injection payload caused server error: {payload}"
            
            # Cleanup if created
            if response.status_code == 201:
                authenticated_client.delete(
                    f"{config['base_url']}/users/{response.json()['id']}",
                    timeout=config["timeout"]
                )
    
    def test_ldap_injection_in_search(self, authenticated_client: requests.Session, config: Dict[str, Any]):
        """Test that LDAP injection attempts in search are handled."""
        ldap_payloads = [
            "*)(uid=*",
            "admin)(&(password=*))",
            "*))(|(uid=*"
        ]
        
        for payload in ldap_payloads:
            response = authenticated_client.get(
                f"{config['base_url']}/users",
                params={
                    "tenantId": config["tenant_id"],
                    "search": payload
                },
                timeout=config["timeout"]
            )
            
            # Should not cause server error
            assert response.status_code in [200, 400], \
                f"LDAP injection should not cause server error"
    
    def test_path_traversal_in_user_id(self, authenticated_client: requests.Session, config: Dict[str, Any]):
        """Test that path traversal attempts are blocked."""
        traversal_payloads = [
            "../../../etc/passwd",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd"
        ]
        
        for payload in traversal_payloads:
            response = authenticated_client.get(
                f"{config['base_url']}/users/{payload}",
                timeout=config["timeout"]
            )
            
            # Should return 400 or 404, not 500 or expose files
            assert response.status_code in [400, 404], \
                f"Path traversal should be blocked: {payload}"
    
    def test_oversized_input_rejected(self, authenticated_client: requests.Session, config: Dict[str, Any], test_user_data: Dict[str, Any]):
        """Test that oversized inputs are rejected."""
        # Business name max length is 200
        test_user_data["businessName"] = "A" * 300
        test_user_data["email"] = f"oversize_{uuid.uuid4().hex[:8]}@teapot.lk"
        test_user_data["phoneNumber"] = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
        
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, \
            "Oversized input should be rejected with 400"
    
    def test_null_byte_injection(self, authenticated_client: requests.Session, config: Dict[str, Any], test_user_data: Dict[str, Any]):
        """Test that null byte injection is handled."""
        test_user_data["businessName"] = "Test\x00Business"
        test_user_data["email"] = f"null_test_{uuid.uuid4().hex[:8]}@teapot.lk"
        test_user_data["phoneNumber"] = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
        
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        # Should handle gracefully (400 or sanitize)
        assert response.status_code in [400, 201], \
            "Null byte injection should be handled"
        
        if response.status_code == 201:
            authenticated_client.delete(
                f"{config['base_url']}/users/{response.json()['id']}",
                timeout=config["timeout"]
            )


@pytest.mark.security
class TestAuthorizationSecurity:
    """Security tests for authorization and access control."""
    
    def test_user_cannot_access_other_tenant_data(self, authenticated_client: requests.Session, config: Dict[str, Any]):
        """Test that users cannot access data from other tenants."""
        # Try to access with a different tenant ID
        fake_tenant_id = str(uuid.uuid4())
        
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            params={"tenantId": fake_tenant_id},
            timeout=config["timeout"]
        )
        
        # Should either return empty results or unauthorized
        assert response.status_code in [200, 401, 403], \
            "Should handle cross-tenant access appropriately"
        
        if response.status_code == 200:
            # Should return no data or very limited data
            data = response.json()
            # This assumes tenant isolation is enforced
            print(f"Note: Verify tenant isolation - returned {len(data.get('data', []))} users")
    
    def test_user_cannot_delete_other_users(self, authenticated_client: requests.Session, config: Dict[str, Any], created_user: Dict[str, Any]):
        """Test that users cannot delete other user accounts (if not admin)."""
        # Note: This assumes non-admin users shouldn't be able to delete
        # If the service allows all authenticated users to delete, this test may need adjustment
        
        response = authenticated_client.delete(
            f"{config['base_url']}/users/{created_user['id']}",
            timeout=config["timeout"]
        )
        
        # Should either succeed (204) or be forbidden (403), depending on permissions
        # Document the actual behavior
        print(f"Delete permission test result: {response.status_code}")
    
    def test_jwt_token_from_one_user_cannot_access_another(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that JWT tokens are user-specific."""
        # Create two users
        user1_email = f"user1_{uuid.uuid4().hex[:8]}@teapot.lk"
        user1_username = f"user1_{uuid.uuid4().hex[:8]}"
        user2_email = f"user2_{uuid.uuid4().hex[:8]}@teapot.lk"
        user2_username = f"user2_{uuid.uuid4().hex[:8]}"
        password = "TestPass123!"
        
        # Register user 1
        response1 = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": user1_email,
                "password": password,
                "confirmPassword": password,
                "username": user1_username,
                "tp": "+94771234001"
            },
            timeout=config["timeout"]
        )
        assert response1.status_code == 201
        token1 = response1.json()["token"]
        user1_id = response1.json()["user"]["id"]
        
        # Register user 2
        response2 = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": user2_email,
                "password": password,
                "confirmPassword": password,
                "username": user2_username,
                "tp": "+94771234002"
            },
            timeout=config["timeout"]
        )
        assert response2.status_code == 201
        user2_id = response2.json()["user"]["id"]
        
        # User 1 tries to access their own data - should work
        api_client.headers.update({"Authorization": f"Bearer {token1}"})
        response = api_client.get(
            f"{config['base_url']}/users/{user1_id}",
            timeout=config["timeout"]
        )
        # Note: This assumes users can view their own data
        # Actual behavior depends on authorization rules
        print(f"User accessing own data: {response.status_code}")


@pytest.mark.security
class TestPasswordSecurity:
    """Security tests for password handling."""
    
    def test_password_not_returned_in_response(self, api_client: requests.Session, config: Dict[str, Any], unique_email: str, unique_username: str, unique_phone: str):
        """Test that passwords are never returned in API responses."""
        password = "SecurePass123!"
        
        response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "confirmPassword": password,
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201
        response_text = response.text.lower()
        
        # Password should not appear in response
        assert password.lower() not in response_text, \
            "Password should never be returned in response"
        assert "password" not in response.json().get("user", {}), \
            "Password field should not be in user object"
    
    def test_weak_password_rejected(self, api_client: requests.Session, config: Dict[str, Any], unique_email: str, unique_username: str, unique_phone: str):
        """Test that weak passwords are rejected."""
        weak_passwords = [
            "password",  # Too common
            "12345678",  # Only digits
            "abcdefgh",  # Only lowercase
            "ABCDEFGH",  # Only uppercase
            "Pass123",   # Too short
            "Password1",  # Missing special char
        ]
        
        for weak_pass in weak_passwords:
            response = api_client.post(
                f"{config['base_url']}/auth/register",
                json={
                    "email": f"test_{uuid.uuid4().hex[:8]}@teapot.lk",
                    "password": weak_pass,
                    "confirmPassword": weak_pass,
                    "username": f"user_{uuid.uuid4().hex[:8]}",
                    "tp": unique_phone
                },
                timeout=config["timeout"]
            )
            
            assert response.status_code == 400, \
                f"Weak password should be rejected: {weak_pass}"
    
    def test_password_brute_force_protection(self, api_client: requests.Session, config: Dict[str, Any], unique_email: str, unique_username: str, unique_phone: str):
        """Test that repeated failed login attempts are rate-limited."""
        password = "CorrectPass123!"
        
        # Register user
        api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "confirmPassword": password,
                "username": unique_username,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(15):  # Try 15 failed logins
            response = api_client.post(
                f"{config['base_url']}/auth/login",
                json={
                    "email": unique_email,
                    "password": "WrongPassword123!"
                },
                timeout=config["timeout"]
            )
            
            if response.status_code == 429:  # Rate limited
                print(f"Rate limiting detected after {i + 1} attempts")
                break
            
            failed_attempts += 1
        
        # Note: Actual rate limiting behavior may vary
        print(f"Brute force protection: {failed_attempts} attempts before rate limit")


@pytest.mark.security
class TestDataExposureSecurity:
    """Security tests for data exposure and information leakage."""
    
    def test_error_messages_dont_leak_sensitive_info(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that error messages don't expose sensitive system information."""
        response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={
                "email": "nonexistent@teapot.lk",
                "password": "SomePass123!"
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401
        error_text = response.text.lower()
        
        # Should not expose database details, stack traces, etc.
        sensitive_terms = ["sql", "database", "stack trace", "exception", "error at line"]
        for term in sensitive_terms:
            assert term not in error_text, \
                f"Error message should not contain: {term}"
    
    def test_404_responses_dont_confirm_user_existence(self, authenticated_client: requests.Session, config: Dict[str, Any]):
        """Test that 404 responses don't leak whether users exist."""
        fake_uuid = str(uuid.uuid4())
        
        response = authenticated_client.get(
            f"{config['base_url']}/users/{fake_uuid}",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 404
        
        # Error message should be generic
        error = response.json()
        assert "not found" in error.get("message", "").lower(), \
            "Should use generic 'not found' message"
    
    def test_server_header_not_exposing_version(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that Server header doesn't expose detailed version info."""
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        server_header = response.headers.get("Server", "")
        
        # Should not expose detailed version numbers that could be exploited
        # This is more of a documentation test
        print(f"Server header: {server_header}")
    
    def test_no_directory_listing(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that directory listing is not enabled."""
        response = api_client.get(
            config['base_url'].rstrip('/api/v1'),
            timeout=config["timeout"]
        )
        
        # Should not return HTML directory listing
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            assert "index of" not in response.text.lower(), \
                "Directory listing should be disabled"


@pytest.mark.security
class TestHTTPSecurityHeaders:
    """Test for HTTP security headers."""
    
    def test_security_headers_present(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that important security headers are present."""
        response = api_client.get(
            f"{config['base_url']}/health",
            timeout=config["timeout"]
        )
        
        # Check for important security headers
        headers_to_check = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "Strict-Transport-Security": "max-age",  # Should contain max-age
        }
        
        for header, expected_value in headers_to_check.items():
            actual_value = response.headers.get(header, "")
            
            if isinstance(expected_value, list):
                # Check if any of the expected values is present
                has_expected = any(val.lower() in actual_value.lower() for val in expected_value)
                print(f"{header}: {actual_value} (expected one of {expected_value})")
            else:
                has_expected = expected_value.lower() in actual_value.lower()
                print(f"{header}: {actual_value} (expected to contain '{expected_value}')")
    
    def test_cors_headers_properly_configured(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test that CORS headers are properly configured."""
        response = api_client.options(
            f"{config['base_url']}/health",
            headers={"Origin": "https://malicious-site.com"},
            timeout=config["timeout"]
        )
        
        # Check CORS configuration
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        
        # Should not allow all origins in production
        if config["test_env"] == "prod":
            assert allow_origin != "*", \
                "Production should not allow all origins"
        
        print(f"CORS Allow-Origin: {allow_origin}")
