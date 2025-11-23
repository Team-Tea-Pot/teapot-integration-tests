#!/bin/bash

# Complete test workflow: Start containers → Run tests → Stop containers
# Usage: ./run_tests.sh [pytest options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.test.yml"
PROJECT_NAME="teapot-integration-tests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CLEANUP_VOLUMES=false
PYTEST_ARGS=("$@")

# If no args provided, default to running all tests
if [ ${#PYTEST_ARGS[@]} -eq 0 ]; then
    PYTEST_ARGS=("tests/" "-v")
fi

# Parse flags
for arg in "$@"; do
    if [ "$arg" = "--cleanup-volumes" ] || [ "$arg" = "-cv" ]; then
        CLEANUP_VOLUMES=true
        # Remove this arg from pytest args
        PYTEST_ARGS=("${PYTEST_ARGS[@]/$arg}")
    fi
done

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  TeaPot Integration Tests - Full Workflow${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Cleanup function to ensure containers stop even on failure
cleanup() {
    EXIT_CODE=$?
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Stopping Containers...${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    CLEANUP_CMD="docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down"
    if [ "$CLEANUP_VOLUMES" = true ]; then
        echo -e "${YELLOW}⚠️  Removing volumes...${NC}"
        CLEANUP_CMD="$CLEANUP_CMD -v"
    fi
    
    eval $CLEANUP_CMD
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  ✅ Tests Completed Successfully!${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
        echo ""
    else
        echo ""
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  ❌ Tests Failed (Exit Code: $EXIT_CODE)${NC}"
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo ""
    fi
    
    exit $EXIT_CODE
}

# Register cleanup function
trap cleanup EXIT INT TERM

# Step 1: Check Docker
echo -e "${BLUE}[1/4]${NC} Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker is running"
echo ""

# Step 2: Start containers
echo -e "${BLUE}[2/4]${NC} Starting containers..."
echo ""
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --remove-orphans

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start containers${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Waiting for containers to be healthy...${NC}"

# Wait for health checks (max 2 minutes)
TIMEOUT=120
ELAPSED=0
INTERVAL=5

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check if all containers are healthy
    UNHEALTHY=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --format json 2>/dev/null | \
                jq -r 'select(.Health != "" and .Health != "healthy") | .Service' 2>/dev/null | wc -l)
    
    NOT_RUNNING=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --format json 2>/dev/null | \
                  jq -r 'select(.State != "running") | .Service' 2>/dev/null | wc -l)
    
    if [ "$UNHEALTHY" -eq 0 ] && [ "$NOT_RUNNING" -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓${NC} All containers are healthy!"
        echo ""
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
        echo ""
        break
    fi
    
    echo -n "."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo ""
    echo -e "${RED}❌ Timeout waiting for containers to be healthy${NC}"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
    echo ""
    echo "Recent logs:"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs --tail=50
    exit 1
fi

# Step 3: Run tests
echo -e "${BLUE}[3/4]${NC} Running tests..."
echo -e "${YELLOW}Command: pytest ${PYTEST_ARGS[*]}${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Set environment variable to skip Docker management in conftest.py
export SKIP_DOCKER=1

# Run pytest with provided arguments
pytest "${PYTEST_ARGS[@]}"

# Store exit code
TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Tests failed with exit code: $TEST_EXIT_CODE${NC}"
    exit $TEST_EXIT_CODE
fi

echo -e "${GREEN}✓${NC} All tests passed!"
echo ""

# Step 4: Cleanup (handled by trap)
echo -e "${BLUE}[4/4]${NC} Cleanup..."

# Exit with test result code (cleanup will run via trap)
exit $TEST_EXIT_CODE
