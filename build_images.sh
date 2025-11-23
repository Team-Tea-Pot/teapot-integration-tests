#!/bin/bash

# Build Docker images required for TeaPot integration tests
# This script builds the user-service image from the platform-builder repo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_BUILDER_DIR="${SCRIPT_DIR}/../tea-pot-platform-builder"

echo "════════════════════════════════════════════════════════════"
echo "  Building TeaPot Docker Images"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if platform builder directory exists
if [ ! -d "$PLATFORM_BUILDER_DIR" ]; then
    echo "❌ Error: Platform builder directory not found: $PLATFORM_BUILDER_DIR"
    echo ""
    echo "Expected location: ../tea-pot-platform-builder"
    echo "Please clone the platform-builder repository to the correct location:"
    echo "  git clone <repo-url> ../tea-pot-platform-builder"
    echo ""
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "📦 Building user-service image..."
echo ""

cd "$PLATFORM_BUILDER_DIR"

# Try using Makefile first
if [ -f "Makefile" ] && grep -q "build-user-service" Makefile; then
    echo "Using Makefile target: build-user-service"
    make build-user-service
elif [ -f "docker-compose.yml" ]; then
    echo "Using docker-compose to build user-service"
    docker compose build user-service
else
    echo "❌ Error: Could not find build method for user-service"
    echo "Please build the image manually in the platform-builder repo"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully built teapot/user-service:latest"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  Image built successfully!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "You can now start the test containers with:"
    echo "  cd $SCRIPT_DIR"
    echo "  ./up_containers.sh"
    echo ""
else
    echo ""
    echo "❌ Failed to build user-service image"
    echo ""
    echo "Try building manually:"
    echo "  cd $PLATFORM_BUILDER_DIR"
    echo "  make build-user-service"
    echo "  # or"
    echo "  docker compose build user-service"
    echo ""
    exit 1
fi
