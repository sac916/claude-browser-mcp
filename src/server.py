"""
MCP Server Implementation for Browser Automation

This module implements the main MCP server that provides browser automation
capabilities through standardized MCP tools. It handles tool registration,
request routing, and response formatting.

The server exposes the following tools:
- navigate_to: Navigate to a URL
- get_page_content: Extract text content from the current page
- click_element: Click on page elements by selector
- fill_form: Fill form fields with data
- take_screenshot: Capture page screenshots
- execute_javascript: Run custom JavaScript code

Usage:
    python -m src.server
    
Environment Variables:
    BROWSER_HEADLESS: Run browser in headless mode (default: true)
    BROWSER_TIMEOUT: Default timeout for operations in seconds (default: 30)
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .browser import BrowserManager
from .actions import BrowserActions
from .utils import sanitize_html, format_error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("browser-automation")

# Global browser manager instance
browser_manager: Optional[BrowserManager] = None
browser_actions: Optional[BrowserActions] = None


@app.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """
    List all available browser automation tools.
    
    Returns:
        List of MCP tool definitions with descriptions and parameters
    """
    return [
        types.Tool(
            name="navigate_to",
            description="Navigate to a specified URL in the browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to"
                    },
                    "wait_for": {
                        "type": "string", 
                        "description": "CSS selector to wait for after navigation (optional)",
                        "default": None
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="get_page_content",
            description="Extract text content from the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_links": {
                        "type": "boolean",
                        "description": "Include link URLs in output (default: false)",
                        "default": False
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to extract content from specific element (optional)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="click_element",
            description="Click on an element specified by CSS selector",
            inputSchema={
                "type": "object", 
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the element to click"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (default: 10)",
                        "default": 10
                    }
                },
                "required": ["selector"]
            }
        ),
        types.Tool(
            name="fill_form",
            description="Fill form fields with specified data",
            inputSchema={
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "object",
                        "description": "Object mapping CSS selectors to values to fill"
                    },
                    "submit": {
                        "type": "boolean", 
                        "description": "Whether to submit the form after filling (default: false)",
                        "default": False
                    }
                },
                "required": ["fields"]
            }
        ),
        types.Tool(
            name="take_screenshot", 
            description="Take a screenshot of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "full_page": {
                        "type": "boolean",
                        "description": "Capture full page height (default: false)",
                        "default": False
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to screenshot specific element (optional)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="execute_javascript",
            description="Execute JavaScript code in the browser context",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "JavaScript code to execute"
                    },
                    "return_value": {
                        "type": "boolean",
                        "description": "Whether to return the result of the execution (default: true)",
                        "default": True
                    }
                },
                "required": ["code"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """
    Handle tool execution requests.
    
    Args:
        name: Name of the tool to execute
        arguments: Tool arguments as provided by the client
        
    Returns:
        Sequence of text content responses
    """
    global browser_manager, browser_actions
    
    try:
        # Initialize browser if needed
        if browser_manager is None or browser_actions is None:
            await initialize_browser()
            
        # Route to appropriate handler
        if name == "navigate_to":
            result = await browser_actions.navigate_to(
                url=arguments["url"],
                wait_for=arguments.get("wait_for"),
                timeout=arguments.get("timeout", 30)
            )
            
        elif name == "get_page_content":
            result = await browser_actions.get_page_content(
                include_links=arguments.get("include_links", False),
                selector=arguments.get("selector")
            )
            
        elif name == "click_element":
            result = await browser_actions.click_element(
                selector=arguments["selector"],
                timeout=arguments.get("timeout", 10)
            )
            
        elif name == "fill_form":
            result = await browser_actions.fill_form(
                fields=arguments["fields"],
                submit=arguments.get("submit", False)
            )
            
        elif name == "take_screenshot":
            result = await browser_actions.take_screenshot(
                full_page=arguments.get("full_page", False),
                selector=arguments.get("selector")
            )
            
        elif name == "execute_javascript":
            result = await browser_actions.execute_javascript(
                code=arguments["code"],
                return_value=arguments.get("return_value", True)
            )
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
        # Format successful response
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        error_response = format_error_response(str(e), name, arguments)
        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]


async def initialize_browser() -> None:
    """
    Initialize the browser manager and actions handler.
    
    This function sets up the global browser instances needed for
    tool execution. Called automatically on first tool use.
    """
    global browser_manager, browser_actions
    
    logger.info("Initializing browser manager...")
    browser_manager = BrowserManager()
    await browser_manager.start()
    
    browser_actions = BrowserActions(browser_manager)
    logger.info("Browser initialization complete")


async def cleanup() -> None:
    """
    Clean up browser resources on server shutdown.
    
    Ensures all browser processes are properly terminated.
    """
    global browser_manager
    
    if browser_manager:
        logger.info("Cleaning up browser resources...")
        await browser_manager.cleanup()


def main():
    """
    Main entry point for the browser MCP server.
    
    Starts the MCP server with stdio transport and handles
    graceful shutdown with browser cleanup.
    """
    async def run_server():
        # Setup initialization options
        init_options = InitializationOptions(
            server_name="browser-automation",
            server_version="0.1.0",
            capabilities=app.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )
        
        try:
            # Run the server
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                logger.info("Starting browser MCP server...")
                await app.run(
                    read_stream,
                    write_stream, 
                    init_options
                )
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
        finally:
            await cleanup()
            logger.info("Server shutdown complete")
    
    # Run the async server
    asyncio.run(run_server())


if __name__ == "__main__":
    main()