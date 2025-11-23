"""
Locust load testing for User Service.
Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8080
"""

from locust import HttpUser, task, between, events
import uuid
import random


class UserServiceUser(HttpUser):
    """Simulates a user interacting with the User Service."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.base_path = "/api/v1"
        self.token = None
        self.user_id = None
        self.tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Register and login
        self.register_and_login()
    
    def register_and_login(self):
        """Register a new user and obtain auth token."""
        email = f"locust_{uuid.uuid4().hex[:8]}@teapot.lk"
        username = f"locust_{uuid.uuid4().hex[:8]}"
        password = "LocustTest123!"
        phone = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
        
        # Register
        response = self.client.post(
            f"{self.base_path}/auth/register",
            json={
                "email": email,
                "password": password,
                "confirmPassword": password,
                "username": username,
                "tp": phone
            },
            name="/auth/register"
        )
        
        if response.status_code == 201:
            self.token = response.json().get("token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(5)
    def health_check(self):
        """Check service health (high frequency)."""
        self.client.get(f"{self.base_path}/health", name="/health")
    
    @task(3)
    def list_users(self):
        """List users with pagination."""
        if not self.token:
            return
        
        page = random.randint(1, 5)
        self.client.get(
            f"{self.base_path}/users",
            params={
                "tenantId": self.tenant_id,
                "page": page,
                "limit": 20
            },
            name="/users (list)"
        )
    
    @task(2)
    def create_user(self):
        """Create a new user profile."""
        if not self.token:
            return
        
        email = f"user_{uuid.uuid4().hex[:8]}@teapot.lk"
        phone = f"+947{uuid.uuid4().hex[:9].replace('a', '7')[:9]}"
        
        response = self.client.post(
            f"{self.base_path}/users",
            json={
                "businessName": f"Test Business {uuid.uuid4().hex[:8]}",
                "ownerName": "Test Owner",
                "email": email,
                "phoneNumber": phone,
                "tenantId": self.tenant_id,
                "farmSizeHectares": random.uniform(5.0, 50.0),
                "location": {
                    "latitude": 6.9271,
                    "longitude": 79.8612,
                    "address": "Nuwara Eliya, Sri Lanka"
                }
            },
            name="/users (create)"
        )
        
        if response.status_code == 201:
            # Store user ID for potential updates/deletes
            self.user_id = response.json()["id"]
    
    @task(2)
    def get_user(self):
        """Get user details by ID."""
        if not self.token or not self.user_id:
            return
        
        self.client.get(
            f"{self.base_path}/users/{self.user_id}",
            name="/users/{userId} (get)"
        )
    
    @task(1)
    def update_user(self):
        """Update user profile."""
        if not self.token or not self.user_id:
            return
        
        self.client.put(
            f"{self.base_path}/users/{self.user_id}",
            json={
                "farmSizeHectares": random.uniform(10.0, 100.0),
                "businessName": f"Updated Business {uuid.uuid4().hex[:4]}"
            },
            name="/users/{userId} (update)"
        )
    
    @task(1)
    def login(self):
        """Perform login (simulates returning users)."""
        email = f"returning_{uuid.uuid4().hex[:8]}@teapot.lk"
        password = "TestPass123!"
        
        # This will mostly fail (user doesn't exist), but simulates login traffic
        self.client.post(
            f"{self.base_path}/auth/login",
            json={
                "email": email,
                "password": password
            },
            name="/auth/login"
        )
    
    @task(1)
    def search_users(self):
        """Search users by business name."""
        if not self.token:
            return
        
        search_terms = ["Tea", "Estate", "Garden", "Plantation", "Ceylon"]
        search = random.choice(search_terms)
        
        self.client.get(
            f"{self.base_path}/users",
            params={
                "tenantId": self.tenant_id,
                "search": search,
                "limit": 10
            },
            name="/users (search)"
        )


class AdminUser(HttpUser):
    """Simulates admin operations."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup admin user."""
        self.base_path = "/api/v1"
        self.token = None
        self.tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Admins would have pre-existing accounts
        self.login_admin()
    
    def login_admin(self):
        """Login as admin."""
        # This assumes an admin account exists
        response = self.client.post(
            f"{self.base_path}/auth/login",
            json={
                "email": "admin@teapot.lk",
                "password": "Admin!Pass123"
            },
            name="/auth/login (admin)"
        )
        
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(5)
    def list_all_users(self):
        """Admin lists all users with various filters."""
        if not self.token:
            return
        
        page = random.randint(1, 10)
        limit = random.choice([10, 20, 50])
        
        self.client.get(
            f"{self.base_path}/users",
            params={
                "tenantId": self.tenant_id,
                "page": page,
                "limit": limit
            },
            name="/users (admin list)"
        )
    
    @task(2)
    def view_user_details(self):
        """Admin views specific user details."""
        if not self.token:
            return
        
        # Use a random UUID (most will 404, simulates admin checking various users)
        user_id = str(uuid.uuid4())
        
        self.client.get(
            f"{self.base_path}/users/{user_id}",
            name="/users/{userId} (admin view)"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("=" * 60)
    print("Starting User Service Load Test")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("=" * 60)
    print("Load Test Completed")
    print("=" * 60)
    
    # Print summary statistics
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/second: {stats.total.total_rps:.2f}")
