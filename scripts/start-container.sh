#!/bin/bash
set -e

# Production-ready container startup script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
IMAGE_NAME="claude-browser-mcp"
CONTAINER_NAME="claude-browser-mcp"
TAG="${1:-latest}"
MODE="${2:-production}"

echo "🚀 Starting browser MCP server container"
echo "🖼️ Image: $IMAGE_NAME:$TAG"
echo "📦 Container: $CONTAINER_NAME"
echo "⚙️ Mode: $MODE"

# Create required directories
cd "$PROJECT_ROOT"
mkdir -p screenshots downloads logs config

# Stop existing container if running
if docker ps -a --format "{{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "🛑 Stopping existing container..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

# Production container startup
if [ "$MODE" = "production" ]; then
    echo "🏭 Starting production container..."
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        --init \
        --ipc=host \
        --shm-size=1gb \
        --memory=2g \
        --cpus=1.0 \
        --security-opt no-new-privileges:true \
        --cap-drop ALL \
        --cap-add SYS_ADMIN \
        --restart unless-stopped \
        -v "$(pwd)/screenshots:/app/screenshots:rw" \
        -v "$(pwd)/downloads:/app/downloads:rw" \
        -v "$(pwd)/logs:/app/logs:rw" \
        -v "$(pwd)/config:/app/config:ro" \
        -e BROWSER_HEADLESS=true \
        -e BROWSER_TIMEOUT=30000 \
        -e MCP_LOG_LEVEL=INFO \
        "$IMAGE_NAME:$TAG"

# Development container startup  
elif [ "$MODE" = "development" ]; then
    echo "🛠️ Starting development container..."
    
    # Enable X11 forwarding on Linux
    XAUTH_FILE="/tmp/.docker.xauth"
    if [ -n "$DISPLAY" ] && command -v xauth >/dev/null; then
        xauth nlist "$DISPLAY" | sed -e 's/^..*/ffff&/' | xauth -f "$XAUTH_FILE" nmerge -
        chmod 644 "$XAUTH_FILE"
        X11_ARGS="-v /tmp/.X11-unix:/tmp/.X11-unix:rw -v $XAUTH_FILE:$XAUTH_FILE:rw -e DISPLAY=$DISPLAY -e XAUTHORITY=$XAUTH_FILE"
    else
        X11_ARGS=""
    fi
    
    docker run -d \
        --name "$CONTAINER_NAME-dev" \
        --init \
        --ipc=host \
        --shm-size=1gb \
        $X11_ARGS \
        -v "$(pwd):/app:rw" \
        -v "$(pwd)/screenshots:/app/screenshots:rw" \
        -v "$(pwd)/downloads:/app/downloads:rw" \
        -v "$(pwd)/logs:/app/logs:rw" \
        -e BROWSER_HEADLESS=false \
        -e BROWSER_TIMEOUT=30000 \
        -e MCP_LOG_LEVEL=DEBUG \
        -p 5678:5678 \
        "$IMAGE_NAME:$TAG-dev"
        
    CONTAINER_NAME="$CONTAINER_NAME-dev"
fi

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 3

# Check if container is running
if docker ps --format "{{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "✅ Container started successfully!"
    
    # Show container status
    echo ""
    echo "📊 Container status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -1
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "$CONTAINER_NAME"
    
    # Show initial logs
    echo ""
    echo "📜 Initial logs:"
    docker logs "$CONTAINER_NAME" 2>&1 | tail -10
    
    echo ""
    echo "🎛️ Useful commands:"
    echo "  View logs: docker logs -f $CONTAINER_NAME"
    echo "  Check health: ./scripts/health-check.sh $CONTAINER_NAME"
    echo "  Stop container: docker stop $CONTAINER_NAME"
    echo "  Enter container: docker exec -it $CONTAINER_NAME /bin/bash"
    
else
    echo "❌ Container failed to start"
    echo "📜 Container logs:"
    docker logs "$CONTAINER_NAME" 2>&1 || true
    exit 1
fi