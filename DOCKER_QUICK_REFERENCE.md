# Quick Reference: Docker Container Management

## 🚀 Quick Start

### One Command to Rule Them All
```bash
# Start containers → Run tests → Stop containers (ALL IN ONE!)
./run_tests.sh

# Run specific tests
./run_tests.sh tests/functional/ -v
./run_tests.sh tests/security/

# Clean up volumes after tests
./run_tests.sh --cleanup-volumes
```

### First Time Setup
```bash
# Build required images (one-time or when updating)
./build_images.sh
```

### Alternative: Automatic with pytest
```bash
# Tests automatically manage containers
pytest tests/
pytest tests/functional/ -v
```

### Manual Container Control
```bash
# Start containers manually
./up_containers.sh

# Stop containers (keep data)
./down_containers.sh

# Stop and remove all data
./down_containers.sh --volumes
```

## 📋 Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| **User Service** | http://localhost:8081 | - |
| **Health Check** | http://localhost:8081/health | - |
| **PostgreSQL** | localhost:5433 | user: `teapot`, pass: `teapot123` |
| **Redis** | localhost:6380 | No auth |

## 🔧 Common Commands

### Check Container Status
```bash
docker compose -f docker-compose.test.yml ps
```

### View Logs
```bash
# All services
docker compose -f docker-compose.test.yml logs -f

# Specific service
docker compose -f docker-compose.test.yml logs -f user-service
```

### Restart a Service
```bash
docker compose -f docker-compose.test.yml restart user-service
```

### Execute Commands in Container
```bash
# PostgreSQL
docker exec -it teapot-test-postgres psql -U teapot -d teapot_users

# Redis
docker exec -it teapot-test-redis redis-cli
```

## 🐛 Troubleshooting

### Containers Won't Start
```bash
# Check Docker is running
docker info

# Check for port conflicts
lsof -i :5433  # PostgreSQL
lsof -i :6380  # Redis
lsof -i :8081  # User Service

# View detailed logs
docker compose -f docker-compose.test.yml logs
```

### Clean Slate
```bash
# Remove everything and start fresh
./down_containers.sh --volumes
docker system prune -f
./up_containers.sh
```

### Skip Docker in Tests
```bash
# Use when containers already running
SKIP_DOCKER=1 pytest tests/
```

## 📦 Python Docker Manager

```python
from tests.docker_manager import DockerManager

# Programmatic control
manager = DockerManager("docker-compose.test.yml")
manager.start_containers()
manager.get_container_status()
manager.stop_containers()
```

### CLI Usage
```bash
# Start containers
python -m tests.docker_manager up

# Check status (JSON output)
python -m tests.docker_manager status

# View logs
python -m tests.docker_manager logs

# Stop containers
python -m tests.docker_manager down --remove-volumes
```

## 🔄 CI/CD Integration

### Environment Variables
```yaml
env:
  SKIP_DOCKER: 0              # Let tests manage Docker
  CLEANUP_VOLUMES: 1          # Clean up after tests
  BASE_URL: http://localhost:8081/api/v1
```

### GitHub Actions Example
```yaml
- name: Start Services
  run: ./up_containers.sh

- name: Run Tests
  run: pytest tests/ -v

- name: Cleanup
  if: always()
  run: ./down_containers.sh --volumes
```

## 📚 More Information

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed documentation.
