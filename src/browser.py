"""
Browser Management Module

This module handles the lifecycle and configuration of Playwright browsers
for the MCP server. It provides a centralized interface for browser operations
including startup, context management, and cleanup.

The BrowserManager class encapsulates all browser-related functionality and
provides a clean interface for other modules to interact with web pages.

Key Features:
- Configurable browser options (headless, viewport, user agent)
- Context isolation for security
- Automatic cleanup and resource management
- Support for multiple browser types (Chromium, Firefox, WebKit)
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Manages Playwright browser instances and contexts.
    
    This class handles the lifecycle of browser processes, providing
    a high-level interface for browser operations while managing
    resources efficiently.
    
    Attributes:
        playwright: Playwright instance
        browser: Current browser instance
        context: Current browser context  
        page: Current active page
        config: Browser configuration options
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the browser manager with optional configuration.
        
        Args:
            config: Optional configuration dictionary with browser settings
        """
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Default configuration
        self.config = {
            "headless": os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            "browser_type": os.getenv("BROWSER_TYPE", "chromium"),
            "viewport": {"width": 1280, "height": 720},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "timeout": int(os.getenv("BROWSER_TIMEOUT", "30000")),
            "downloads_path": str(Path.home() / "Downloads"),
            "ignore_https_errors": True
        }
        
        # Override with provided config
        if config:
            self.config.update(config)
            
        logger.info(f"Browser manager initialized with config: {self.config}")
    
    async def start(self) -> None:
        """
        Start the browser with configured options.
        
        Initializes Playwright, launches browser, creates context and page.
        Must be called before using any browser functionality.
        
        Raises:
            RuntimeError: If browser fails to start or is already running
        """
        if self.playwright is not None:
            raise RuntimeError("Browser is already running")
            
        try:
            logger.info("Starting Playwright browser...")
            self.playwright = await async_playwright().start()
            
            # Get browser type
            browser_type = getattr(self.playwright, self.config["browser_type"])
            
            # Launch browser with options
            launch_options = {
                "headless": self.config["headless"],
                "args": [
                    "--no-sandbox", 
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security"
                ]
            }
            
            self.browser = await browser_type.launch(**launch_options)
            
            # Create browser context
            context_options = {
                "viewport": self.config["viewport"],
                "user_agent": self.config["user_agent"],
                "ignore_https_errors": self.config["ignore_https_errors"]
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Set default timeout
            self.context.set_default_timeout(self.config["timeout"])
            
            # Create initial page
            self.page = await self.context.new_page()
            
            logger.info(f"Browser started successfully: {self.config['browser_type']}")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            await self.cleanup()
            raise RuntimeError(f"Browser startup failed: {str(e)}")
    
    async def get_current_page(self) -> Page:
        """
        Get the current active page.
        
        Returns:
            Current Page instance
            
        Raises:
            RuntimeError: If browser is not started or no page available
        """
        if not self.page:
            if not self.context:
                raise RuntimeError("Browser not started. Call start() first.")
            self.page = await self.context.new_page()
            
        return self.page
    
    async def new_page(self) -> Page:
        """
        Create a new page in the current context.
        
        Returns:
            New Page instance
            
        Raises:
            RuntimeError: If browser is not started
        """
        if not self.context:
            raise RuntimeError("Browser not started. Call start() first.")
            
        new_page = await self.context.new_page()
        self.page = new_page  # Set as current page
        
        logger.info("Created new page")
        return new_page
    
    async def get_all_pages(self) -> List[Page]:
        """
        Get all open pages in the current context.
        
        Returns:
            List of all Page instances
            
        Raises:
            RuntimeError: If browser is not started
        """
        if not self.context:
            raise RuntimeError("Browser not started. Call start() first.")
            
        return self.context.pages
    
    async def close_page(self, page: Optional[Page] = None) -> None:
        """
        Close a specific page or the current page.
        
        Args:
            page: Page to close. If None, closes current page.
        """
        target_page = page or self.page
        
        if target_page:
            await target_page.close()
            logger.info("Page closed")
            
            # If we closed the current page, set to another or create new
            if target_page == self.page:
                pages = await self.get_all_pages()
                if pages:
                    self.page = pages[0]
                else:
                    self.page = None
    
    async def set_viewport(self, width: int, height: int) -> None:
        """
        Set viewport size for the current page.
        
        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
        """
        if not self.page:
            raise RuntimeError("No active page available")
            
        await self.page.set_viewport_size({"width": width, "height": height})
        self.config["viewport"] = {"width": width, "height": height}
        
        logger.info(f"Viewport set to {width}x{height}")
    
    async def set_user_agent(self, user_agent: str) -> None:
        """
        Set user agent for the current context.
        
        Args:
            user_agent: User agent string to set
        """
        if not self.context:
            raise RuntimeError("Browser not started")
            
        # Note: Playwright requires creating new context to change user agent
        # This is a limitation of the underlying browser engines
        logger.warning("User agent change requires restart for full effect")
        self.config["user_agent"] = user_agent
    
    async def enable_request_interception(self) -> None:
        """
        Enable request interception for the current page.
        
        Allows monitoring and modifying network requests.
        """
        if not self.page:
            raise RuntimeError("No active page available")
            
        await self.page.route("**/*", self._handle_route)
        logger.info("Request interception enabled")
    
    async def _handle_route(self, route, request) -> None:
        """
        Default route handler for intercepted requests.
        
        Args:
            route: Playwright route object
            request: Playwright request object
        """
        # Default behavior: continue with request
        await route.continue_()
    
    async def get_browser_info(self) -> Dict[str, Any]:
        """
        Get information about the current browser instance.
        
        Returns:
            Dictionary containing browser information
        """
        if not self.browser:
            return {"status": "not_started"}
            
        contexts = len(self.browser.contexts)
        pages = len(await self.get_all_pages()) if self.context else 0
        
        return {
            "status": "running",
            "browser_type": self.config["browser_type"],
            "headless": self.config["headless"],
            "contexts": contexts,
            "pages": pages,
            "current_url": await self.page.url() if self.page else None,
            "viewport": self.config["viewport"]
        }
    
    async def cleanup(self) -> None:
        """
        Clean up all browser resources.
        
        Closes all pages, contexts, and the browser instance.
        Should be called when shutting down the server.
        """
        logger.info("Cleaning up browser resources...")
        
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close() 
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Browser cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during browser cleanup: {str(e)}")
    
    async def restart(self) -> None:
        """
        Restart the browser with current configuration.
        
        Useful for recovering from errors or applying new settings.
        """
        logger.info("Restarting browser...")
        await self.cleanup()
        await self.start()
        logger.info("Browser restart complete")