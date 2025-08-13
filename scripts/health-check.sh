#!/bin/bash
set -e

# Health check script for browser MCP server container
# Can be used standalone or as part of Docker health checks

CONTAINER_NAME="${1:-claude-browser-mcp}"
TIMEOUT="${2:-10}"

echo "🔍 Checking health of container: $CONTAINER_NAME"

# Check if container is running
if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "❌ Container $CONTAINER_NAME is not running"
    exit 1
fi

# Check container health status
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "none")

echo "🏥 Health status: $HEALTH_STATUS"

case "$HEALTH_STATUS" in
    "healthy")
        echo "✅ Container is healthy"
        ;;
    "unhealthy")
        echo "❌ Container is unhealthy"
        echo "📋 Recent health check logs:"
        docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' "$CONTAINER_NAME" | tail -5
        exit 1
        ;;
    "starting")
        echo "🔄 Container is starting, health check in progress"
        ;;
    "none")
        echo "⚠️ No health check configured, performing basic checks..."
        
        # Basic process check
        if docker exec "$CONTAINER_NAME" pgrep -f "python.*src.server" >/dev/null; then
            echo "✅ MCP server process is running"
        else
            echo "❌ MCP server process not found"
            exit 1
        fi
        
        # Memory usage check
        MEMORY_USAGE=$(docker stats --no-stream --format "{{.MemPerc}}" "$CONTAINER_NAME")
        echo "📊 Memory usage: $MEMORY_USAGE"
        ;;
esac

# Check logs for errors
echo "📜 Recent logs (last 10 lines):"
docker logs --tail 10 "$CONTAINER_NAME" 2>&1 | head -10

# Resource usage summary
echo ""
echo "📊 Resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" "$CONTAINER_NAME"

echo "✅ Health check completed"