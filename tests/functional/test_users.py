"""
Functional tests for user management endpoints.
Tests /users, /users/{userId}, /users/register, and /users/{userId}/verify endpoints.
"""

import pytest
import requests
import uuid


@pytest.mark.functional
@pytest.mark.users
class TestCreateUser:
    """Test suite for POST /users endpoint."""
    
    def test_create_user_success(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test successful user creation with valid data."""
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        # Cleanup
        if response.status_code == 201:
            user_id = response.json()["id"]
            authenticated_client.delete(f"{config['base_url']}/users/{user_id}", timeout=config["timeout"])
    
    def test_create_user_response_structure(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test that created user response has correct structure."""
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201
        user = response.json()
        
        # Verify required fields
        required_fields = ["id", "businessName", "ownerName", "email", "phoneNumber", 
                          "tenantId", "isActive", "isVerified", "createdAt", "updatedAt"]
        for field in required_fields:
            assert field in user, f"Response missing required field: {field}"
        
        # Cleanup
        authenticated_client.delete(f"{config['base_url']}/users/{user['id']}", timeout=config["timeout"])
    
    def test_create_user_validates_data(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test that created user data matches request."""
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201
        user = response.json()
        
        assert user["businessName"] == test_user_data["businessName"]
        assert user["ownerName"] == test_user_data["ownerName"]
        assert user["email"] == test_user_data["email"]
        assert user["phoneNumber"] == test_user_data["phoneNumber"]
        assert user["tenantId"] == test_user_data["tenantId"]
        
        # Cleanup
        authenticated_client.delete(f"{config['base_url']}/users/{user['id']}", timeout=config["timeout"])
    
    def test_create_user_with_duplicate_email(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test that duplicate email returns 409 conflict."""
        # Create first user
        response1 = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        assert response1.status_code == 201
        user1 = response1.json()
        
        # Try to create second user with same email
        test_user_data["phoneNumber"] = "+94771999888"
        response2 = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response2.status_code == 409, f"Expected 409, got {response2.status_code}"
        
        # Cleanup
        authenticated_client.delete(f"{config['base_url']}/users/{user1['id']}", timeout=config["timeout"])
    
    def test_create_user_with_invalid_email(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test that invalid email format returns 400."""
        test_user_data["email"] = "not-an-email"
        
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_create_user_with_missing_required_field(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test that missing required field returns 400."""
        del test_user_data["businessName"]
        
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_create_user_without_auth(self, api_client: requests.Session, config: dict, test_user_data: dict):
        """Test that creating user without auth returns 401."""
        response = api_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_create_user_with_location_data(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test creating user with location information."""
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201
        user = response.json()
        
        assert user["location"] is not None
        assert user["location"]["latitude"] == test_user_data["location"]["latitude"]
        assert user["location"]["longitude"] == test_user_data["location"]["longitude"]
        
        # Cleanup
        authenticated_client.delete(f"{config['base_url']}/users/{user['id']}", timeout=config["timeout"])
    
    def test_create_user_with_invalid_farm_size(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test that invalid farm size returns 400."""
        test_user_data["farmSizeHectares"] = -5.0  # Negative value
        
        response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


@pytest.mark.functional
@pytest.mark.users
class TestListUsers:
    """Test suite for GET /users endpoint."""
    
    def test_list_users_success(self, authenticated_client: requests.Session, config: dict):
        """Test listing users with required tenantId."""
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            params={"tenantId": config["tenant_id"]},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_list_users_response_structure(self, authenticated_client: requests.Session, config: dict):
        """Test that list users returns correct structure."""
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            params={"tenantId": config["tenant_id"]},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data, "Response missing 'data' field"
        assert "pagination" in data, "Response missing 'pagination' field"
        assert isinstance(data["data"], list), "data should be a list"
    
    def test_list_users_pagination_fields(self, authenticated_client: requests.Session, config: dict):
        """Test that pagination object has required fields."""
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            params={"tenantId": config["tenant_id"]},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        pagination = response.json()["pagination"]
        
        required_fields = ["page", "limit", "total", "totalPages"]
        for field in required_fields:
            assert field in pagination, f"Pagination missing field: {field}"
    
    def test_list_users_with_pagination(self, authenticated_client: requests.Session, config: dict):
        """Test listing users with pagination parameters."""
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            params={
                "tenantId": config["tenant_id"],
                "page": 1,
                "limit": 10
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
        assert len(data["data"]) <= 10
    
    def test_list_users_with_search(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test searching users by business name."""
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            params={
                "tenantId": config["tenant_id"],
                "search": created_user["businessName"][:5]
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find at least the created user
        assert isinstance(data["data"], list)
    
    def test_list_users_without_tenant_id(self, authenticated_client: requests.Session, config: dict):
        """Test that listing users without tenantId returns 400."""
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_list_users_without_auth(self, api_client: requests.Session, config: dict):
        """Test that listing users without auth returns 401."""
        response = api_client.get(
            f"{config['base_url']}/users",
            params={"tenantId": config["tenant_id"]},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_list_users_with_invalid_page(self, authenticated_client: requests.Session, config: dict):
        """Test that invalid page number returns 400."""
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            params={
                "tenantId": config["tenant_id"],
                "page": 0  # Invalid: minimum is 1
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_list_users_with_excessive_limit(self, authenticated_client: requests.Session, config: dict):
        """Test that limit over 100 returns 400."""
        response = authenticated_client.get(
            f"{config['base_url']}/users",
            params={
                "tenantId": config["tenant_id"],
                "limit": 101  # Exceeds maximum of 100
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


@pytest.mark.functional
@pytest.mark.users
class TestGetUser:
    """Test suite for GET /users/{userId} endpoint."""
    
    def test_get_user_by_id_success(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test getting user by ID returns correct data."""
        user_id = created_user["id"]
        
        response = authenticated_client.get(
            f"{config['base_url']}/users/{user_id}",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        user = response.json()
        
        assert user["id"] == user_id
        assert user["email"] == created_user["email"]
    
    def test_get_user_with_invalid_uuid(self, authenticated_client: requests.Session, config: dict):
        """Test getting user with invalid UUID format."""
        response = authenticated_client.get(
            f"{config['base_url']}/users/not-a-uuid",
            timeout=config["timeout"]
        )
        
        # Should return 400 (bad request) or 404 (not found)
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
    
    def test_get_nonexistent_user(self, authenticated_client: requests.Session, config: dict):
        """Test getting non-existent user returns 404."""
        fake_uuid = str(uuid.uuid4())
        
        response = authenticated_client.get(
            f"{config['base_url']}/users/{fake_uuid}",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_get_user_without_auth(self, api_client: requests.Session, config: dict, created_user: dict):
        """Test getting user without authentication returns 401."""
        response = api_client.get(
            f"{config['base_url']}/users/{created_user['id']}",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.functional
@pytest.mark.users
class TestUpdateUser:
    """Test suite for PUT /users/{userId} endpoint."""
    
    def test_update_user_success(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test successful user update."""
        user_id = created_user["id"]
        update_data = {
            "businessName": "Updated Tea Estates Ltd",
            "farmSizeHectares": 25.0
        }
        
        response = authenticated_client.put(
            f"{config['base_url']}/users/{user_id}",
            json=update_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        updated_user = response.json()
        
        assert updated_user["businessName"] == update_data["businessName"]
        assert updated_user["farmSizeHectares"] == update_data["farmSizeHectares"]
    
    def test_update_user_location(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test updating user location."""
        user_id = created_user["id"]
        update_data = {
            "location": {
                "latitude": 7.2906,
                "longitude": 80.6337,
                "address": "Kandy, Central Province, Sri Lanka"
            }
        }
        
        response = authenticated_client.put(
            f"{config['base_url']}/users/{user_id}",
            json=update_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 200
        updated_user = response.json()
        
        assert updated_user["location"]["latitude"] == update_data["location"]["latitude"]
        assert updated_user["location"]["address"] == update_data["location"]["address"]
    
    def test_update_nonexistent_user(self, authenticated_client: requests.Session, config: dict):
        """Test updating non-existent user returns 404."""
        fake_uuid = str(uuid.uuid4())
        update_data = {"businessName": "New Name"}
        
        response = authenticated_client.put(
            f"{config['base_url']}/users/{fake_uuid}",
            json=update_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_update_user_with_invalid_data(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test updating user with invalid data returns 400."""
        user_id = created_user["id"]
        update_data = {"farmSizeHectares": -10.0}  # Invalid negative value
        
        response = authenticated_client.put(
            f"{config['base_url']}/users/{user_id}",
            json=update_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_update_user_without_auth(self, api_client: requests.Session, config: dict, created_user: dict):
        """Test updating user without auth returns 401."""
        update_data = {"businessName": "New Name"}
        
        response = api_client.put(
            f"{config['base_url']}/users/{created_user['id']}",
            json=update_data,
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.functional
@pytest.mark.users
class TestDeleteUser:
    """Test suite for DELETE /users/{userId} endpoint."""
    
    def test_delete_user_success(self, authenticated_client: requests.Session, config: dict, test_user_data: dict):
        """Test successful user deletion (soft delete)."""
        # Create a user to delete
        create_response = authenticated_client.post(
            f"{config['base_url']}/users",
            json=test_user_data,
            timeout=config["timeout"]
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Delete the user
        response = authenticated_client.delete(
            f"{config['base_url']}/users/{user_id}",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"
        assert len(response.content) == 0, "204 response should have no content"
    
    def test_delete_nonexistent_user(self, authenticated_client: requests.Session, config: dict):
        """Test deleting non-existent user returns 404."""
        fake_uuid = str(uuid.uuid4())
        
        response = authenticated_client.delete(
            f"{config['base_url']}/users/{fake_uuid}",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_delete_user_without_auth(self, api_client: requests.Session, config: dict, created_user: dict):
        """Test deleting user without auth returns 401."""
        response = api_client.delete(
            f"{config['base_url']}/users/{created_user['id']}",
            timeout=config["timeout"]
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_delete_user_with_invalid_uuid(self, authenticated_client: requests.Session, config: dict):
        """Test deleting user with invalid UUID format."""
        response = authenticated_client.delete(
            f"{config['base_url']}/users/invalid-uuid",
            timeout=config["timeout"]
        )
        
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"


@pytest.mark.functional
@pytest.mark.users
class TestVerifyUser:
    """Test suite for POST /users/{userId}/verify endpoint."""
    
    def test_verify_user_with_valid_code(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test user verification with valid 6-digit code."""
        user_id = created_user["id"]
        
        response = authenticated_client.post(
            f"{config['base_url']}/users/{user_id}/verify",
            json={"verificationCode": "123456"},
            timeout=config["timeout"]
        )
        
        # Should return 200 or 400 depending on whether the code is actually valid in the system
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"
    
    def test_verify_user_with_invalid_code_format(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test verification fails with invalid code format."""
        user_id = created_user["id"]
        
        response = authenticated_client.post(
            f"{config['base_url']}/users/{user_id}/verify",
            json={"verificationCode": "12345"},  # Only 5 digits
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_verify_user_with_non_numeric_code(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test verification fails with non-numeric code."""
        user_id = created_user["id"]
        
        response = authenticated_client.post(
            f"{config['base_url']}/users/{user_id}/verify",
            json={"verificationCode": "abcdef"},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_verify_nonexistent_user(self, authenticated_client: requests.Session, config: dict):
        """Test verifying non-existent user returns 404."""
        fake_uuid = str(uuid.uuid4())
        
        response = authenticated_client.post(
            f"{config['base_url']}/users/{fake_uuid}/verify",
            json={"verificationCode": "123456"},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_verify_user_missing_code(self, authenticated_client: requests.Session, config: dict, created_user: dict):
        """Test verification fails when code is missing."""
        user_id = created_user["id"]
        
        response = authenticated_client.post(
            f"{config['base_url']}/users/{user_id}/verify",
            json={},
            timeout=config["timeout"]
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


@pytest.mark.functional
@pytest.mark.users
class TestRegisterUserAccount:
    """Test suite for POST /users/register endpoint (public registration)."""
    
    def test_register_user_account_success(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test successful public user registration."""
        response = api_client.post(
            f"{config['base_url']}/users/register",
            json={
                "username": unique_username,
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
                "email": unique_email,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        user = response.json()
        
        assert "id" in user
        assert user["email"] == unique_email
    
    def test_register_user_no_auth_required(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test that public registration doesn't require authentication."""
        # Create a clean session without auth headers
        clean_session = requests.Session()
        clean_session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        response = clean_session.post(
            f"{config['base_url']}/users/register",
            json={
                "username": unique_username,
                "password": "TestPass123!",
                "confirmPassword": "TestPass123!",
                "email": unique_email,
                "tp": unique_phone
            },
            timeout=config["timeout"]
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    
    def test_register_duplicate_username(self, api_client: requests.Session, config: dict, unique_email: str, unique_username: str, unique_phone: str):
        """Test registration fails with duplicate username."""
        register_data = {
            "username": unique_username,
            "password": "TestPass123!",
            "confirmPassword": "TestPass123!",
            "email": unique_email,
            "tp": unique_phone
        }
        
        # First registration
        response1 = api_client.post(
            f"{config['base_url']}/users/register",
            json=register_data,
            timeout=config["timeout"]
        )
        assert response1.status_code == 201
        
        # Second registration with same username but different email
        register_data["email"] = f"other_{unique_email}"
        register_data["tp"] = f"+947{unique_phone[4:]}"
        response2 = api_client.post(
            f"{config['base_url']}/users/register",
            json=register_data,
            timeout=config["timeout"]
        )
        
        assert response2.status_code == 409, f"Expected 409, got {response2.status_code}"
