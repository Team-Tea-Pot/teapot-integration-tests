#!/bin/bash

# Stop Docker containers for TeaPot integration tests
# This script provides manual control for stopping test containers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.test.yml"
PROJECT_NAME="teapot-integration-tests"

echo "======================================"
echo "Stopping TeaPot Test Containers"
echo "======================================"
echo ""

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: docker-compose.test.yml not found"
    exit 1
fi

echo "📦 Using compose file: $COMPOSE_FILE"
echo "🏷️  Project name: $PROJECT_NAME"
echo ""

# Parse command line arguments
REMOVE_VOLUMES=false
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        -h|--help)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

if [ "$SHOW_HELP" = true ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -v, --volumes    Remove volumes (cleans database data)"
    echo "  -h, --help       Show this help message"
    echo ""
    exit 0
fi

# Stop containers
echo "🛑 Stopping containers..."

if [ "$REMOVE_VOLUMES" = true ]; then
    echo "⚠️  Removing volumes (this will delete all data)"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down -v
else
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Containers stopped successfully"
    echo ""
    
    if [ "$REMOVE_VOLUMES" = false ]; then
        echo "💾 Volumes preserved (data retained)"
        echo "   To remove volumes, run: $0 --volumes"
    else
        echo "🗑️  Volumes removed (data deleted)"
    fi
    echo ""
else
    echo ""
    echo "❌ Failed to stop containers"
    exit 1
fi
