"""
Pytest configuration and shared fixtures for TeaPot User Service tests.
"""

import os
import pytest
import requests
from typing import Generator, Dict, Any
from dotenv import load_dotenv
import uuid
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)


@pytest.fixture(scope="session", autouse=True)
def docker_containers():
    """
    Automatically start and stop Docker containers for the entire test session.
    This fixture runs once before all tests and cleans up after all tests complete.
    
    Set SKIP_DOCKER=1 environment variable to skip Docker management
    (useful when containers are already running or testing against remote services).
    """
    # Check if Docker management should be skipped
    skip_docker = os.getenv("SKIP_DOCKER", "0").lower() in ("1", "true", "yes")
    
    if skip_docker:
        logging.info("Skipping Docker container management (SKIP_DOCKER is set)")
        yield
        return
    
    # Import docker_manager here to avoid import errors if docker is not installed
    try:
        from tests.docker_manager import DockerManager
    except ImportError as e:
        logging.warning(f"Could not import DockerManager: {e}")
        logging.warning("Skipping Docker container management. Install docker package or set SKIP_DOCKER=1")
        yield
        return
    
    compose_file = os.path.join(
        os.path.dirname(__file__),
        "docker-compose.test.yml"
    )
    
    manager = DockerManager(compose_file=compose_file)
    
    # Check if Docker is available
    if not manager.is_docker_available():
        logging.warning("Docker is not available. Skipping container management.")
        logging.warning("Tests may fail if services are not running.")
        yield
        return
    
    # Start containers
    logging.info("=" * 60)
    logging.info("Starting Docker containers for integration tests...")
    logging.info("=" * 60)
    
    success = manager.start_containers(timeout=120)
    
    if not success:
        logging.error("Failed to start Docker containers!")
        logging.error("Please check Docker logs for details.")
        pytest.exit("Docker containers failed to start", returncode=1)
    
    logging.info("✓ Docker containers are ready!")
    logging.info("=" * 60)
    
    # Run all tests
    yield manager
    
    # Cleanup after all tests
    logging.info("=" * 60)
    logging.info("Stopping Docker containers...")
    logging.info("=" * 60)
    
    # Keep volumes by default, remove with CLEANUP_VOLUMES=1
    remove_volumes = os.getenv("CLEANUP_VOLUMES", "0").lower() in ("1", "true", "yes")
    manager.stop_containers(remove_volumes=remove_volumes)
    
    logging.info("✓ Docker containers stopped")
    logging.info("=" * 60)


@pytest.fixture(scope="session")
def config() -> Dict[str, Any]:
    """Load test configuration from environment variables."""
    env = os.getenv("TEST_ENV", "local")
    
    base_urls = {
        "local": os.getenv("BASE_URL", "http://localhost:8081/api/v1"),  # Updated to match docker-compose.test.yml port
        "dev": os.getenv("DEV_BASE_URL", "https://api-dev.teapot.lk/api/v1"),
        "prod": os.getenv("PROD_BASE_URL", "https://api.teapot.lk/api/v1"),
    }
    
    return {
        "base_url": base_urls.get(env, base_urls["local"]),
        "test_env": env,
        "timeout": int(os.getenv("REQUEST_TIMEOUT", "30")),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "test_user": {
            "email": os.getenv("TEST_USER_EMAIL", "test@teapot.lk"),
            "password": os.getenv("TEST_USER_PASSWORD", "Test!Pass123"),
            "username": os.getenv("TEST_USER_USERNAME", "test.user"),
            "phone": os.getenv("TEST_USER_PHONE", "+94771234567"),
        },
        "admin": {
            "email": os.getenv("ADMIN_EMAIL", "admin@teapot.lk"),
            "password": os.getenv("ADMIN_PASSWORD", "Admin!Pass123"),
            "token": os.getenv("ADMIN_TOKEN", ""),
        },
        "tenant_id": os.getenv("TEST_TENANT_ID", str(uuid.uuid4())),
    }


@pytest.fixture(scope="session")
def api_client(config: Dict[str, Any]) -> requests.Session:
    """Create a configured requests session for API calls."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    return session


@pytest.fixture(scope="function")
def unique_email() -> str:
    """Generate a unique email for testing."""
    return f"test+{uuid.uuid4().hex[:8]}@teapot.lk"


@pytest.fixture(scope="function")
def unique_username() -> str:
    """Generate a unique username for testing."""
    return f"user_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def unique_phone() -> str:
    """Generate a unique phone number for testing."""
    random_digits = uuid.uuid4().hex[:9].replace('a', '7').replace('b', '7')[:9]
    return f"+947{random_digits}"


@pytest.fixture(scope="function")
def auth_token(api_client: requests.Session, config: Dict[str, Any]) -> str:
    """
    Authenticate and return a valid JWT token.
    Creates a new user if needed, then logs in.
    """
    base_url = config["base_url"]
    
    # Try to login with test credentials
    login_response = api_client.post(
        f"{base_url}/auth/login",
        json={
            "email": config["test_user"]["email"],
            "password": config["test_user"]["password"],
        },
        timeout=config["timeout"],
    )
    
    # If login fails (user doesn't exist), register first
    if login_response.status_code == 401:
        register_response = api_client.post(
            f"{base_url}/auth/register",
            json={
                "email": config["test_user"]["email"],
                "password": config["test_user"]["password"],
                "confirmPassword": config["test_user"]["password"],
                "username": config["test_user"]["username"],
                "tp": config["test_user"]["phone"],
            },
            timeout=config["timeout"],
        )
        
        if register_response.status_code == 201:
            return register_response.json()["token"]
        elif register_response.status_code == 409:
            # User exists but login failed, might be wrong password
            pytest.skip("Test user exists but credentials are invalid")
        else:
            pytest.skip(f"Failed to register test user: {register_response.text}")
    
    if login_response.status_code == 200:
        return login_response.json()["token"]
    
    pytest.skip(f"Failed to obtain auth token: {login_response.text}")


@pytest.fixture(scope="function")
def authenticated_client(api_client: requests.Session, auth_token: str) -> requests.Session:
    """Return an authenticated API client with JWT token."""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


@pytest.fixture(scope="function")
def test_user_data(unique_email: str, unique_username: str, unique_phone: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate complete test user data for registration/creation."""
    return {
        "businessName": "Test Tea Estates Ltd",
        "ownerName": "Test Owner",
        "email": unique_email,
        "phoneNumber": unique_phone,
        "username": unique_username,
        "password": "TestPass123!",
        "confirmPassword": "TestPass123!",
        "tenantId": config["tenant_id"],
        "farmSizeHectares": 15.5,
        "location": {
            "latitude": 6.9271,
            "longitude": 79.8612,
            "address": "Test Estate, Nuwara Eliya, Sri Lanka"
        },
        "preferredLanguage": "en"
    }


@pytest.fixture(scope="function")
def created_user(authenticated_client: requests.Session, config: Dict[str, Any], test_user_data: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    Create a test user and return the response.
    Automatically cleans up (deletes) the user after the test.
    """
    base_url = config["base_url"]
    
    # Create user
    response = authenticated_client.post(
        f"{base_url}/users",
        json=test_user_data,
        timeout=config["timeout"],
    )
    
    if response.status_code != 201:
        pytest.skip(f"Failed to create test user: {response.text}")
    
    user = response.json()
    
    yield user
    
    # Cleanup: delete the user
    try:
        authenticated_client.delete(
            f"{base_url}/users/{user['id']}",
            timeout=config["timeout"],
        )
    except Exception as e:
        print(f"Warning: Failed to cleanup test user {user['id']}: {e}")


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "functional: marks tests as functional integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on file path
        if "functional" in str(item.fspath):
            item.add_marker(pytest.mark.functional)
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        if "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
