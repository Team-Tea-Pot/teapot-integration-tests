# TeaPot Integration Tests

Comprehensive integration testing suite for the TeaPot platform, including functional, performance, and security tests.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Python 3.8+
- TeaPot platform-builder repository (for building images)

### Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Build Docker images (first time):**
```bash
./build_images.sh
```

3. **Run tests (one command!):**
```bash
# Single command: starts containers → runs tests → stops containers
./run_tests.sh

# Run specific tests
./run_tests.sh tests/functional/ -v
./run_tests.sh tests/security/
./run_tests.sh --cleanup-volumes  # Remove volumes after tests
```

That's it! The `run_tests.sh` script handles everything automatically.

## 📋 Test Categories

### Functional Tests
```bash
./run_tests.sh tests/functional/ -v
```
Tests for:
- Authentication & Authorization
- User Management
- API Endpoints
- Data Validation

### Security Tests
```bash
./run_tests.sh tests/security/ -v
```
Tests for:
- SQL Injection
- XSS Attacks
- Authentication Bypass
- Rate Limiting

### Performance Tests
```bash
./run_tests.sh tests/performance/ -v
```
Tests for:
- API Response Times
- Load Testing with Locust
- Database Performance
- Concurrent Users

## 🐳 Docker Container Management

### Single Command (Recommended)
```bash
# Everything in one command!
./run_tests.sh              # Run all tests
./run_tests.sh tests/functional/  # Run specific tests
./run_tests.sh --cleanup-volumes  # Clean up volumes after
```

### Alternative Methods

**Automatic (pytest manages containers):**
```bash
pytest tests/  # Containers auto-start/stop
```

**Manual Control:**
```bash
./up_containers.sh              # Start containers
./down_containers.sh            # Stop containers
./down_containers.sh --volumes  # Stop and remove data
```

See [DOCKER_QUICK_REFERENCE.md](DOCKER_QUICK_REFERENCE.md) for more commands.

## 🔧 Configuration

### Environment Variables
Create a `.env` file or set environment variables:

```bash
# Test Environment
TEST_ENV=local                    # local, dev, prod
BASE_URL=http://localhost:8081/api/v1

# Docker Management
SKIP_DOCKER=0                     # Set to 1 to skip Docker management
CLEANUP_VOLUMES=0                 # Set to 1 to remove volumes after tests

# Test User Credentials
TEST_USER_EMAIL=test@teapot.lk
TEST_USER_PASSWORD=Test!Pass123
```

### Service Endpoints
When containers are running:
- **User Service**: http://localhost:8081
- **PostgreSQL**: localhost:5433 (user: `teapot`, pass: `teapot123`)
- **Redis**: localhost:6380

## 📊 Test Reports

Tests generate comprehensive reports:

```bash
# HTML Report
pytest tests/ --html=reports/report.html

# Coverage Report
pytest tests/ --cov=tests --cov-report=html

# JUnit XML (for CI)
pytest tests/ --junitxml=reports/junit.xml
```

## 🛠️ Development

### Project Structure
```
teapot-integration-tests/
├── tests/
│   ├── functional/          # Functional integration tests
│   ├── performance/         # Performance & load tests
│   ├── security/            # Security tests
│   ├── docker_manager.py    # Docker container management
│   └── utils.py             # Test utilities
├── conftest.py              # Pytest fixtures & configuration
├── docker-compose.test.yml  # Test container definitions
├── up_containers.sh         # Start containers script
├── down_containers.sh       # Stop containers script
└── build_images.sh          # Build Docker images script
```

### Adding New Tests

1. Create test file in appropriate directory
2. Use fixtures from `conftest.py`
3. Follow naming convention: `test_*.py`

Example:
```python
def test_new_feature(api_client, config):
    """Test description."""
    response = api_client.get(f"{config['base_url']}/endpoint")
    assert response.status_code == 200
```

## 📚 Documentation

- [DOCKER_QUICK_REFERENCE.md](DOCKER_QUICK_REFERENCE.md) - Quick Docker commands
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Detailed Docker setup guide
- [TEST_SUMMARY.md](TEST_SUMMARY.md) - Test suite overview
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Testing quick reference

## 🔍 Troubleshooting

### Containers won't start
```bash
# Check Docker is running
docker info

# Check for port conflicts
lsof -i :5433 :6380 :8081

# View logs
docker compose -f docker-compose.test.yml logs
```

### Tests fail with connection errors
```bash
# Ensure containers are healthy
./up_containers.sh

# Check health endpoint
curl http://localhost:8081/health
```

### Clean slate
```bash
# Remove everything and restart
./down_containers.sh --volumes
docker system prune -f
./build_images.sh
./up_containers.sh
```

## 🤝 Contributing

1. Write tests for new features
2. Ensure all tests pass
3. Update documentation
4. Submit pull request

## 📝 License

[Your License Here]
