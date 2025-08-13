#!/bin/bash
set -e

# Docker build script for browser MCP server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
IMAGE_NAME="claude-browser-mcp"
TAG="${1:-latest}"
BUILD_TARGET="${2:-production}"

echo "🔨 Building Docker image: $IMAGE_NAME:$TAG"
echo "📁 Project root: $PROJECT_ROOT"
echo "🎯 Target: $BUILD_TARGET"

# Build the image
cd "$PROJECT_ROOT"

if [ "$BUILD_TARGET" = "development" ]; then
    echo "🛠️ Building development image..."
    docker build \
        --target development \
        --build-arg USER_ID=$(id -u) \
        --build-arg GROUP_ID=$(id -g) \
        -f Dockerfile.dev \
        -t "$IMAGE_NAME:$TAG-dev" \
        .
    echo "✅ Development image built: $IMAGE_NAME:$TAG-dev"
else
    echo "🚀 Building production image..."
    docker build \
        --target production \
        -f Dockerfile \
        -t "$IMAGE_NAME:$TAG" \
        .
    echo "✅ Production image built: $IMAGE_NAME:$TAG"
fi

# Show image size
echo ""
echo "📊 Image size:"
docker images | grep "$IMAGE_NAME" | head -1

echo ""
echo "🎉 Build complete!"
echo ""
echo "Usage:"
echo "  Production: docker run --init --ipc=host --shm-size=1gb $IMAGE_NAME:$TAG"
echo "  Development: docker-compose --profile dev up browser-mcp-dev"