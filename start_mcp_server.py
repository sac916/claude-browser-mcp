#!/usr/bin/env python3
"""
MCP Server Startup Script

This script starts the browser automation MCP server with proper environment setup.
It ensures the virtual environment is activated and all dependencies are available.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the MCP server with proper environment setup"""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    
    # Path to virtual environment
    venv_path = script_dir / "venv"
    
    # Check if virtual environment exists
    if not venv_path.exists():
        print("❌ Virtual environment not found. Please run setup first.", file=sys.stderr)
        sys.exit(1)
    
    # Path to Python in virtual environment
    if os.name == 'nt':  # Windows
        python_path = venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux
        python_path = venv_path / "bin" / "python"
    
    if not python_path.exists():
        print(f"❌ Python not found in virtual environment: {python_path}", file=sys.stderr)
        sys.exit(1)
    
    # Set working directory
    os.chdir(script_dir)
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "BROWSER_HEADLESS": "true",
        "BROWSER_TIMEOUT": "30"
    })
    
    # Start the server
    try:
        subprocess.run([
            str(python_path), "-m", "src.server"
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()