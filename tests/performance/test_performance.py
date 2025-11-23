"""
Performance tests for User Service endpoints.
Uses pytest-benchmark to measure response times and throughput.
"""

import pytest
import requests
import time
from typing import Dict, Any


@pytest.mark.performance
@pytest.mark.slow
class TestHealthPerformance:
    """Performance tests for health check endpoint."""
    
    def test_health_check_response_time(self, api_client: requests.Session, config: Dict[str, Any], benchmark):
        """Benchmark health check endpoint response time."""
        def make_request():
            response = api_client.get(
                f"{config['base_url']}/health",
                timeout=config["timeout"]
            )
            assert response.status_code == 200
            return response
        
        result = benchmark(make_request)
        
        # Assert reasonable response time (< 500ms)
        assert benchmark.stats['mean'] < 0.5, \
            f"Health check too slow: {benchmark.stats['mean']:.3f}s average"
    
    def test_health_check_concurrent_requests(self, api_client: requests.Session, config: Dict[str, Any]):
        """Test health check can handle concurrent requests."""
        import concurrent.futures
        
        num_requests = 50
        
        def make_request():
            response = api_client.get(
                f"{config['base_url']}/health",
                timeout=config["timeout"]
            )
            return response.status_code
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        elapsed_time = time.time() - start_time
        
        # All requests should succeed
        assert all(status == 200 for status in results), "Some requests failed"
        
        # Calculate throughput
        throughput = num_requests / elapsed_time
        print(f"\nThroughput: {throughput:.2f} requests/second")
        
        # Should handle at least 10 req/s
        assert throughput > 10, f"Throughput too low: {throughput:.2f} req/s"


@pytest.mark.performance
@pytest.mark.slow
class TestAuthPerformance:
    """Performance tests for authentication endpoints."""
    
    def test_login_response_time(self, api_client: requests.Session, config: Dict[str, Any], benchmark):
        """Benchmark login endpoint response time."""
        # Setup: ensure test user exists
        test_email = config["test_user"]["email"]
        test_password = config["test_user"]["password"]
        
        # Try to register (ignore if already exists)
        api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "confirmPassword": test_password,
                "username": config["test_user"]["username"],
                "tp": config["test_user"]["phone"]
            },
            timeout=config["timeout"]
        )
        
        def make_login_request():
            response = api_client.post(
                f"{config['base_url']}/auth/login",
                json={
                    "email": test_email,
                    "password": test_password
                },
                timeout=config["timeout"]
            )
            assert response.status_code == 200
            return response
        
        result = benchmark(make_login_request)
        
        # Login should complete within 2 seconds
        assert benchmark.stats['mean'] < 2.0, \
            f"Login too slow: {benchmark.stats['mean']:.3f}s average"
    
    def test_register_response_time(self, api_client: requests.Session, config: Dict[str, Any], benchmark, unique_email: str, unique_username: str, unique_phone: str):
        """Benchmark registration endpoint response time."""
        
        def make_register_request():
            import uuid
            email = f"perf_test_{uuid.uuid4().hex[:8]}@teapot.lk"
            username = f"perfuser_{uuid.uuid4().hex[:8]}"
            phone = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
            
            response = api_client.post(
                f"{config['base_url']}/auth/register",
                json={
                    "email": email,
                    "password": "PerfTest123!",
                    "confirmPassword": "PerfTest123!",
                    "username": username,
                    "tp": phone
                },
                timeout=config["timeout"]
            )
            assert response.status_code == 201
            return response
        
        result = benchmark(make_register_request)
        
        # Registration should complete within 3 seconds (includes hashing)
        assert benchmark.stats['mean'] < 3.0, \
            f"Registration too slow: {benchmark.stats['mean']:.3f}s average"


@pytest.mark.performance
@pytest.mark.slow
class TestUserOperationsPerformance:
    """Performance tests for user CRUD operations."""
    
    def test_create_user_response_time(self, authenticated_client: requests.Session, config: Dict[str, Any], test_user_data: Dict[str, Any], benchmark):
        """Benchmark user creation endpoint."""
        created_user_ids = []
        
        def make_create_request():
            import uuid
            # Create unique data for each iteration
            data = test_user_data.copy()
            data["email"] = f"perf_{uuid.uuid4().hex[:8]}@teapot.lk"
            data["phoneNumber"] = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
            
            response = authenticated_client.post(
                f"{config['base_url']}/users",
                json=data,
                timeout=config["timeout"]
            )
            
            if response.status_code == 201:
                created_user_ids.append(response.json()["id"])
            
            assert response.status_code == 201
            return response
        
        result = benchmark(make_create_request)
        
        # Cleanup created users
        for user_id in created_user_ids:
            try:
                authenticated_client.delete(
                    f"{config['base_url']}/users/{user_id}",
                    timeout=config["timeout"]
                )
            except:
                pass
        
        # User creation should complete within 2 seconds
        assert benchmark.stats['mean'] < 2.0, \
            f"User creation too slow: {benchmark.stats['mean']:.3f}s average"
    
    def test_get_user_response_time(self, authenticated_client: requests.Session, config: Dict[str, Any], created_user: Dict[str, Any], benchmark):
        """Benchmark get user by ID endpoint."""
        user_id = created_user["id"]
        
        def make_get_request():
            response = authenticated_client.get(
                f"{config['base_url']}/users/{user_id}",
                timeout=config["timeout"]
            )
            assert response.status_code == 200
            return response
        
        result = benchmark(make_get_request)
        
        # Read operations should be fast (< 500ms)
        assert benchmark.stats['mean'] < 0.5, \
            f"Get user too slow: {benchmark.stats['mean']:.3f}s average"
    
    def test_list_users_response_time(self, authenticated_client: requests.Session, config: Dict[str, Any], benchmark):
        """Benchmark list users endpoint."""
        
        def make_list_request():
            response = authenticated_client.get(
                f"{config['base_url']}/users",
                params={
                    "tenantId": config["tenant_id"],
                    "page": 1,
                    "limit": 20
                },
                timeout=config["timeout"]
            )
            assert response.status_code == 200
            return response
        
        result = benchmark(make_list_request)
        
        # List operations should complete within 1 second
        assert benchmark.stats['mean'] < 1.0, \
            f"List users too slow: {benchmark.stats['mean']:.3f}s average"
    
    def test_update_user_response_time(self, authenticated_client: requests.Session, config: Dict[str, Any], created_user: Dict[str, Any], benchmark):
        """Benchmark user update endpoint."""
        user_id = created_user["id"]
        
        def make_update_request():
            response = authenticated_client.put(
                f"{config['base_url']}/users/{user_id}",
                json={
                    "businessName": f"Updated Business {time.time()}",
                    "farmSizeHectares": 20.0 + (time.time() % 10)
                },
                timeout=config["timeout"]
            )
            assert response.status_code == 200
            return response
        
        result = benchmark(make_update_request)
        
        # Update should complete within 1 second
        assert benchmark.stats['mean'] < 1.0, \
            f"Update user too slow: {benchmark.stats['mean']:.3f}s average"
    
    def test_user_operations_under_load(self, authenticated_client: requests.Session, config: Dict[str, Any], test_user_data: Dict[str, Any]):
        """Test user operations can handle sustained load."""
        import concurrent.futures
        import uuid
        
        num_operations = 20
        created_user_ids = []
        
        def create_user():
            data = test_user_data.copy()
            data["email"] = f"load_test_{uuid.uuid4().hex[:8]}@teapot.lk"
            data["phoneNumber"] = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
            
            response = authenticated_client.post(
                f"{config['base_url']}/users",
                json=data,
                timeout=config["timeout"]
            )
            
            if response.status_code == 201:
                return response.json()["id"], response.status_code
            return None, response.status_code
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_user) for _ in range(num_operations)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        elapsed_time = time.time() - start_time
        
        # Extract successful creations
        created_user_ids = [user_id for user_id, status in results if user_id is not None]
        success_count = len(created_user_ids)
        
        # Cleanup
        for user_id in created_user_ids:
            try:
                authenticated_client.delete(
                    f"{config['base_url']}/users/{user_id}",
                    timeout=config["timeout"]
                )
            except:
                pass
        
        # Calculate metrics
        throughput = num_operations / elapsed_time
        success_rate = (success_count / num_operations) * 100
        
        print(f"\nLoad test results:")
        print(f"  Total operations: {num_operations}")
        print(f"  Successful: {success_count}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Throughput: {throughput:.2f} ops/second")
        print(f"  Total time: {elapsed_time:.2f}s")
        
        # Should handle at least 70% success rate under load
        assert success_rate >= 70, f"Success rate too low: {success_rate:.1f}%"


@pytest.mark.performance
@pytest.mark.slow
class TestEndToEndPerformance:
    """End-to-end performance scenarios."""
    
    def test_complete_user_lifecycle_time(self, api_client: requests.Session, config: Dict[str, Any]):
        """Measure time for complete user lifecycle: register -> login -> create profile -> update -> delete."""
        import uuid
        
        email = f"e2e_perf_{uuid.uuid4().hex[:8]}@teapot.lk"
        username = f"e2euser_{uuid.uuid4().hex[:8]}"
        phone = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
        password = "E2ETest123!"
        
        start_time = time.time()
        
        # Step 1: Register
        register_response = api_client.post(
            f"{config['base_url']}/auth/register",
            json={
                "email": email,
                "password": password,
                "confirmPassword": password,
                "username": username,
                "tp": phone
            },
            timeout=config["timeout"]
        )
        assert register_response.status_code == 201
        token = register_response.json()["token"]
        
        # Step 2: Login
        login_response = api_client.post(
            f"{config['base_url']}/auth/login",
            json={"email": email, "password": password},
            timeout=config["timeout"]
        )
        assert login_response.status_code == 200
        
        # Step 3: Create user profile
        auth_client = requests.Session()
        auth_client.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        })
        
        create_response = auth_client.post(
            f"{config['base_url']}/users",
            json={
                "businessName": "E2E Performance Test Estate",
                "ownerName": "E2E Test Owner",
                "email": f"business_{email}",
                "phoneNumber": f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}",
                "tenantId": config["tenant_id"],
                "farmSizeHectares": 15.5
            },
            timeout=config["timeout"]
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Step 4: Update user
        update_response = auth_client.put(
            f"{config['base_url']}/users/{user_id}",
            json={"farmSizeHectares": 20.0},
            timeout=config["timeout"]
        )
        assert update_response.status_code == 200
        
        # Step 5: Get user
        get_response = auth_client.get(
            f"{config['base_url']}/users/{user_id}",
            timeout=config["timeout"]
        )
        assert get_response.status_code == 200
        
        # Step 6: Delete user
        delete_response = auth_client.delete(
            f"{config['base_url']}/users/{user_id}",
            timeout=config["timeout"]
        )
        assert delete_response.status_code == 204
        
        total_time = time.time() - start_time
        
        print(f"\nComplete lifecycle time: {total_time:.2f}s")
        
        # Complete lifecycle should finish within 10 seconds
        assert total_time < 10.0, f"Lifecycle too slow: {total_time:.2f}s"
