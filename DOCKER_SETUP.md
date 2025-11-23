# Docker Container Management for Integration Tests

This document describes how to manage Docker containers for TeaPot integration tests.

## Overview

The integration tests require three services to be running:
- **PostgreSQL** (teapot/postgres) - Database on port 5433
- **Redis** (teapot/redis) - Cache on port 6380  
- **User Service** (teapot/user-service) - Go backend on port 8081

All services are defined in `docker-compose.test.yml` and use separate ports from development to avoid conflicts.

## Automatic Container Management (Recommended)

By default, when you run tests with `pytest`, the containers are **automatically started before tests** and **stopped after tests complete**. No manual intervention needed!

```bash
# Just run tests - containers managed automatically
pytest tests/

# Or with specific markers
pytest tests/functional/ -v
```

### Environment Variables

Control automatic Docker management with these variables:

- `SKIP_DOCKER=1` - Skip Docker management (use when containers already running)
- `CLEANUP_VOLUMES=1` - Remove volumes when stopping containers (deletes all data)

```bash
# Run tests without Docker management
SKIP_DOCKER=1 pytest tests/

# Run tests and clean up volumes afterward
CLEANUP_VOLUMES=1 pytest tests/
```

## Manual Container Management

For development or debugging, you can manually control containers:

### Start Containers

```bash
# Using the convenience script
./up_containers.sh

# Or using docker compose directly
docker compose -f docker-compose.test.yml -p teapot-integration-tests up -d
```

### Stop Containers

```bash
# Stop containers (keep volumes/data)
./down_containers.sh

# Stop containers and remove volumes (delete all data)
./down_containers.sh --volumes
```

### View Container Status

```bash
# Check running containers
docker compose -f docker-compose.test.yml -p teapot-integration-tests ps

# View logs
docker compose -f docker-compose.test.yml -p teapot-integration-tests logs

# Follow logs
docker compose -f docker-compose.test.yml -p teapot-integration-tests logs -f

# Logs for specific service
docker compose -f docker-compose.test.yml -p teapot-integration-tests logs user-service
```

### Restart Specific Service

```bash
docker compose -f docker-compose.test.yml -p teapot-integration-tests restart user-service
```

## Using Python Docker Manager

The `tests/docker_manager.py` module provides programmatic container management:

```python
from tests.docker_manager import DockerManager

# Create manager
manager = DockerManager("docker-compose.test.yml")

# Start containers
manager.start_containers()

# Check status
status = manager.get_container_status()

# Stop containers
manager.stop_containers(remove_volumes=False)
```

### CLI Usage

```bash
# Start containers
python -m tests.docker_manager up

# Stop containers
python -m tests.docker_manager down

# Stop and remove volumes
python -m tests.docker_manager down --remove-volumes

# Check status
python -m tests.docker_manager status

# View logs
python -m tests.docker_manager logs

# Restart specific service
python -m tests.docker_manager restart --service user-service
```

## Service Endpoints

When containers are running:

| Service | Endpoint | Credentials |
|---------|----------|-------------|
| PostgreSQL | `localhost:5433` | user: `teapot`, password: `teapot123`, db: `teapot_users` |
| Redis | `localhost:6380` | No auth |
| User Service API | `http://localhost:8081/api/v1` | - |
| Health Check | `http://localhost:8081/health` | - |

## Troubleshooting

### Containers won't start

1. Check if Docker is running:
   ```bash
   docker info
   ```

2. Check for port conflicts:
   ```bash
   lsof -i :5433  # PostgreSQL
   lsof -i :6380  # Redis
   lsof -i :8081  # User Service
   ```

3. View detailed logs:
   ```bash
   docker compose -f docker-compose.test.yml -p teapot-integration-tests logs
   ```

### Health checks failing

Wait a bit longer - services need time to initialize:
- PostgreSQL: ~10 seconds
- Redis: ~5 seconds
- User Service: ~30 seconds (depends on database migrations)

### Clean slate

Remove everything and start fresh:
```bash
./down_containers.sh --volumes
./up_containers.sh
```

### Image not found

The user-service image needs to be built from the platform-builder repo:

```bash
cd ../tea-pot-platform-builder
make build-user-service
# or
docker compose -f docker-compose.yml build user-service
```

## Network Architecture

All containers run in the `teapot-test-network` bridge network. Services can communicate using their service names:
- `postgres:5432` (internal)
- `redis:6379` (internal)
- `user-service:8080` (internal)

External access uses mapped ports on localhost (5433, 6380, 8081).

## Volumes

Data is persisted in named volumes:
- `teapot-test-postgres-data` - PostgreSQL data
- `teapot-test-redis-data` - Redis data

These volumes persist between container restarts unless explicitly removed with `--volumes` flag.

## Integration with CI/CD

In CI environments (GitHub Actions, GitLab CI, etc.), set environment variables:

```yaml
# GitHub Actions example
env:
  SKIP_DOCKER: 0  # Let tests manage Docker
  CLEANUP_VOLUMES: 1  # Clean up after tests
  BASE_URL: http://localhost:8081/api/v1
```

The pytest fixtures will handle container lifecycle automatically.
