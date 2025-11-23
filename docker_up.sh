#!/bin/bash

# Start Docker containers for TeaPot integration tests
# This script provides manual control for starting test containers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.test.yml"
PROJECT_NAME="teapot-integration-tests"

echo "======================================"
echo "Starting TeaPot Test Containers"
echo "======================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: docker-compose.test.yml not found"
    exit 1
fi

echo "📦 Using compose file: $COMPOSE_FILE"
echo "🏷️  Project name: $PROJECT_NAME"
echo ""

# Start containers
echo "🚀 Starting containers..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --build --remove-orphans

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Failed to start containers"
    exit 1
fi

echo ""
echo "⏳ Waiting for containers to be healthy..."
echo ""

# Wait for containers to be healthy
MAX_WAIT=120
ELAPSED=0
INTERVAL=2

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Check container health
    UNHEALTHY=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --format json | \
        jq -r 'select(.Health != "" and .Health != "healthy") | .Service' 2>/dev/null | wc -l | tr -d ' ')
    
    STOPPED=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --format json | \
        jq -r 'select(.State != "running") | .Service' 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$UNHEALTHY" = "0" ] && [ "$STOPPED" = "0" ]; then
        echo ""
        echo "✅ All containers are healthy and running!"
        echo ""
        echo "======================================"
        echo "Container Status"
        echo "======================================"
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
        echo ""
        echo "======================================"
        echo "Service Endpoints"
        echo "======================================"
        echo "PostgreSQL:    localhost:5433"
        echo "Redis:         localhost:6380"
        echo "User Service:  http://localhost:8081"
        echo "Health Check:  http://localhost:8081/health"
        echo "API Base:      http://localhost:8081/api/v1"
        echo ""
        echo "✅ Ready to run tests!"
        echo ""
        exit 0
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
    echo -n "."
done

echo ""
echo "⚠️  Warning: Containers did not become healthy within ${MAX_WAIT}s"
echo ""
echo "Container Status:"
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
echo ""
echo "Recent logs:"
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs --tail=20
echo ""
echo "Containers may still be starting. Check logs with:"
echo "  docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f"

exit 1
