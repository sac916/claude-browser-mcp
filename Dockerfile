# Multi-stage build for optimized browser automation MCP server
FROM python:3.12-slim as builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in builder stage
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage with official Playwright image
FROM mcr.microsoft.com/playwright:v1.54.0-noble as production

# Install Python and pip (Playwright image has Node.js but may not have Python)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3 /usr/bin/python

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser \
    && mkdir -p /app/screenshots /app/downloads /app/logs /app/tmp \
    && chown -R mcpuser:mcpuser /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/mcpuser/.local

# Set up Python environment
ENV PATH="/home/mcpuser/.local/bin:${PATH}"
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Playwright configuration for containers
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# MCP server configuration
ENV MCP_LOG_LEVEL=INFO
ENV BROWSER_HEADLESS=true
ENV BROWSER_TIMEOUT=30000
ENV BROWSER_TYPE=chromium

# Set working directory and copy application
WORKDIR /app
COPY --chown=mcpuser:mcpuser src/ ./src/
COPY --chown=mcpuser:mcpuser setup.py README.md ./

# Install the application package
USER root
RUN pip install -e . --break-system-packages
USER mcpuser

# Create entrypoint script for better process handling
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Function to handle shutdown gracefully
cleanup() {
    echo "Shutting down MCP server..."
    kill -TERM "$child" 2>/dev/null || true
    wait "$child"
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start the MCP server
echo "Starting browser MCP server..."
python -m src.server &
child=$!

# Wait for the process
wait "$child"
EOF

RUN chmod +x /app/entrypoint.sh

# Health check to ensure server is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app'); from src.browser import BrowserManager; print('OK')" || exit 1

# Expose any ports if needed (MCP uses stdio by default)
# EXPOSE 8931

# Use init process to handle zombie processes
ENTRYPOINT ["/app/entrypoint.sh"]