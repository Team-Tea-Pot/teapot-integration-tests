#!/bin/bash

# Stop Docker containers for TeaPot integration tests
# This script brings down postgres, redis, and user-service containers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.test.yml"
PROJECT_NAME="teapot-integration-tests"

echo "════════════════════════════════════════════════════════════"
echo "  Stopping TeaPot Integration Test Containers"
echo "════════════════════════════════════════════════════════════"
echo ""

# Parse command line arguments
REMOVE_VOLUMES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes    Remove volumes (deletes all data)"
            echo "  -h, --help       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: docker-compose file not found: $COMPOSE_FILE"
    exit 1
fi

echo "📦 Stopping containers..."
echo ""

# Build the docker compose command
CMD="docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down"

if [ "$REMOVE_VOLUMES" = true ]; then
    echo "⚠️  WARNING: This will remove all volumes and delete data!"
    CMD="$CMD -v"
fi

# Execute the command
eval $CMD

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Containers stopped successfully"
    
    if [ "$REMOVE_VOLUMES" = true ]; then
        echo "✅ Volumes removed"
    else
        echo "ℹ️  Volumes preserved (use -v flag to remove)"
    fi
    
    echo ""
    echo "════════════════════════════════════════════════════════════"
    exit 0
else
    echo ""
    echo "❌ Failed to stop containers"
    exit 1
fi
