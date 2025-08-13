#!/bin/bash
# Wrapper script to run browser MCP server in Docker for Claude Code
set -e

# Configuration
IMAGE_NAME="claude-browser-mcp-browser-mcp"
CONTAINER_NAME="browser-mcp-$(date +%s)"
PROJECT_DIR="/home/gmitch/claude-browser-mcp"

# Ensure directories exist
mkdir -p "$PROJECT_DIR/screenshots" "$PROJECT_DIR/downloads"

# Cleanup function
cleanup() {
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

# Set up cleanup on exit
trap cleanup EXIT

# Run the MCP server container
docker run \
    --name "$CONTAINER_NAME" \
    --init \
    --ipc=host \
    --shm-size=1gb \
    --memory=2g \
    --cpus=1.0 \
    -v "$PROJECT_DIR/screenshots:/app/screenshots:rw" \
    -v "$PROJECT_DIR/downloads:/app/downloads:rw" \
    -e BROWSER_HEADLESS=true \
    -e BROWSER_TIMEOUT=30000 \
    -e MCP_LOG_LEVEL=INFO \
    "$IMAGE_NAME" \
    python -m src.server