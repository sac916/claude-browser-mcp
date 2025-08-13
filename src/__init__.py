"""
Browser MCP Server

A Model Context Protocol (MCP) server that provides browser automation capabilities
using Playwright. This package enables AI assistants to interact with web pages
through standardized MCP tools for navigation, content extraction, and interaction.

Main Components:
- server.py: MCP server implementation and tool registration
- browser.py: Playwright browser management and configuration
- actions.py: High-level browser actions and interactions
- utils.py: Utility functions for data processing and conversion

Author: Claude Assistant
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Claude Assistant"
__description__ = "Browser automation MCP server using Playwright"

from .server import main
from .browser import BrowserManager
from .actions import BrowserActions
from .utils import sanitize_html, take_screenshot

__all__ = [
    "main",
    "BrowserManager", 
    "BrowserActions",
    "sanitize_html",
    "take_screenshot"
]