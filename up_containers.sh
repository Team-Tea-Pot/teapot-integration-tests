#!/bin/bash

# Start Docker containers for TeaPot integration tests
# This script brings up postgres, redis, and user-service for testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.test.yml"
PROJECT_NAME="teapot-integration-tests"

echo "════════════════════════════════════════════════════════════"
echo "  Starting TeaPot Integration Test Containers"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: docker-compose file not found: $COMPOSE_FILE"
    exit 1
fi

echo "📦 Starting containers..."
echo ""

# Start containers
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --remove-orphans 2>&1 | grep -v "Exception in thread" || true

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  Waiting for containers to be healthy..."
    echo "════════════════════════════════════════════════════════════"
    echo ""
    
    # Wait for health checks (max 2 minutes)
    TIMEOUT=120
    ELAPSED=0
    INTERVAL=5
    
    while [ $ELAPSED -lt $TIMEOUT ]; do
        # Check container health
        UNHEALTHY=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --format json | \
                    jq -r 'select(.Health != "healthy" and .State == "running") | .Service' 2>/dev/null | wc -l)
        
        NOT_RUNNING=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --format json | \
                      jq -r 'select(.State != "running") | .Service' 2>/dev/null | wc -l)
        
        if [ "$UNHEALTHY" -eq 0 ] && [ "$NOT_RUNNING" -eq 0 ]; then
            echo ""
            echo "✅ All containers are healthy and running!"
            echo ""
            echo "════════════════════════════════════════════════════════════"
            echo "  Container Information"
            echo "════════════════════════════════════════════════════════════"
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
            echo ""
            echo "════════════════════════════════════════════════════════════"
            echo "  Service Endpoints"
            echo "════════════════════════════════════════════════════════════"
            echo "  PostgreSQL:    localhost:5433"
            echo "  Redis:         localhost:6380"
            echo "  User Service:  http://localhost:8081"
            echo "  Health Check:  http://localhost:8081/health"
            echo "════════════════════════════════════════════════════════════"
            echo ""
            exit 0
        fi
        
        echo -n "."
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done
    
    echo ""
    echo "⚠️  Warning: Timeout waiting for containers to be healthy"
    echo ""
    echo "Container status:"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
    echo ""
    echo "Recent logs:"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs --tail=20
    echo ""
    echo "Containers started but may not be fully healthy yet."
    echo "Check logs with: docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs"
    exit 1
else
    echo ""
    echo "❌ Failed to start containers"
    exit 1
fi
