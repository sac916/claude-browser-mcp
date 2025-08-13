#!/bin/bash
# MCP Server startup script for Claude Code integration

set -e
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start the MCP server
exec python -m src.server