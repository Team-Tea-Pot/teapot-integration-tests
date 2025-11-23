"""
Utility functions for testing.
"""

import uuid
import random
import string
from typing import Dict, Any


def generate_unique_email(prefix: str = "test") -> str:
    """Generate a unique email address for testing."""
    return f"{prefix}+{uuid.uuid4().hex[:8]}@teapot.lk"


def generate_unique_username(prefix: str = "user") -> str:
    """Generate a unique username for testing."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def generate_unique_phone(country_code: str = "+94") -> str:
    """Generate a unique phone number for testing."""
    random_digits = ''.join(random.choices(string.digits, k=9))
    return f"{country_code}{random_digits}"


def generate_strong_password(length: int = 12) -> str:
    """Generate a strong password that meets requirements."""
    # Must have: uppercase, lowercase, digit, special char
    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice("!@#$%^&*()_+-=")
    
    # Fill the rest randomly
    remaining_length = length - 4
    remaining = ''.join(random.choices(
        string.ascii_letters + string.digits + "!@#$%^&*()_+-=",
        k=remaining_length
    ))
    
    # Combine and shuffle
    password_chars = list(uppercase + lowercase + digit + special + remaining)
    random.shuffle(password_chars)
    
    return ''.join(password_chars)


def create_test_user_payload(
    email: str = None,
    username: str = None,
    phone: str = None,
    tenant_id: str = None
) -> Dict[str, Any]:
    """Create a complete test user payload."""
    return {
        "businessName": f"Test Business {uuid.uuid4().hex[:8]}",
        "ownerName": "Test Owner",
        "email": email or generate_unique_email(),
        "phoneNumber": phone or generate_unique_phone(),
        "tenantId": tenant_id or str(uuid.uuid4()),
        "farmSizeHectares": round(random.uniform(5.0, 100.0), 2),
        "location": {
            "latitude": round(random.uniform(5.0, 10.0), 4),
            "longitude": round(random.uniform(79.0, 82.0), 4),
            "address": "Test Estate, Nuwara Eliya, Sri Lanka"
        },
        "preferredLanguage": random.choice(["en", "si", "ta"])
    }


def create_registration_payload(
    email: str = None,
    username: str = None,
    phone: str = None,
    password: str = None
) -> Dict[str, Any]:
    """Create a registration payload."""
    pwd = password or generate_strong_password()
    return {
        "email": email or generate_unique_email(),
        "password": pwd,
        "confirmPassword": pwd,
        "username": username or generate_unique_username(),
        "tp": phone or generate_unique_phone()
    }


def validate_user_response(user: Dict[str, Any]) -> bool:
    """Validate that a user response has all required fields."""
    required_fields = [
        "id", "businessName", "ownerName", "email", "phoneNumber",
        "tenantId", "isActive", "isVerified", "createdAt", "updatedAt"
    ]
    
    return all(field in user for field in required_fields)


def validate_pagination_response(response: Dict[str, Any]) -> bool:
    """Validate that a pagination response has correct structure."""
    if "data" not in response or "pagination" not in response:
        return False
    
    pagination = response["pagination"]
    required_pagination_fields = ["page", "limit", "total", "totalPages"]
    
    return all(field in pagination for field in required_pagination_fields)


def extract_error_message(response) -> str:
    """Extract error message from response."""
    try:
        error_data = response.json()
        return error_data.get("message", response.text)
    except:
        return response.text


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def is_valid_jwt(token: str) -> bool:
    """Check if a string looks like a valid JWT token."""
    if not token or not isinstance(token, str):
        return False
    
    parts = token.split('.')
    return len(parts) == 3 and all(len(part) > 0 for part in parts)
