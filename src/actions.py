"""
Browser Actions Module

This module provides high-level browser actions and interactions for the MCP server.
It implements the core functionality that clients can access through MCP tools,
abstracting complex browser operations into simple, reliable methods.

The BrowserActions class serves as the primary interface between the MCP server
and the browser manager, handling tasks like navigation, content extraction,
form filling, and screenshot capture.

Key Features:
- URL navigation with smart waiting strategies
- Content extraction with customizable selectors
- Form automation and input handling  
- Screenshot capture with flexible options
- JavaScript execution with result handling
- Robust error handling and logging
"""

import asyncio
import base64
import json
import logging
import re
from io import BytesIO
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .browser import BrowserManager
from .utils import sanitize_html, extract_text_content, is_valid_url

logger = logging.getLogger(__name__)


class BrowserActions:
    """
    High-level browser actions interface.
    
    This class provides methods for common browser automation tasks,
    abstracting the complexity of direct Playwright interactions into
    simple, reliable operations suitable for MCP tool exposure.
    
    Attributes:
        browser_manager: BrowserManager instance for browser control
    """
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize browser actions with a browser manager.
        
        Args:
            browser_manager: Initialized BrowserManager instance
        """
        self.browser_manager = browser_manager
        logger.info("BrowserActions initialized")
    
    async def navigate_to(self, url: str, wait_for: Optional[str] = None, 
                         timeout: int = 30) -> Dict[str, Any]:
        """
        Navigate to a specified URL.
        
        Args:
            url: Target URL to navigate to
            wait_for: Optional CSS selector to wait for after navigation
            timeout: Timeout in seconds for navigation
            
        Returns:
            Dictionary containing navigation result and page information
            
        Raises:
            ValueError: If URL is invalid
            RuntimeError: If navigation fails
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL provided: {url}")
            
        try:
            page = await self.browser_manager.get_current_page()
            
            logger.info(f"Navigating to: {url}")
            
            # Navigate with timeout
            response = await page.goto(url, timeout=timeout * 1000)
            
            if not response:
                raise RuntimeError(f"Failed to get response for URL: {url}")
                
            # Wait for additional selector if specified
            if wait_for:
                logger.info(f"Waiting for selector: {wait_for}")
                await page.wait_for_selector(wait_for, timeout=timeout * 1000)
            
            # Get page information
            title = await page.title()
            final_url = page.url
            status = response.status
            
            result = {
                "success": True,
                "url": final_url,
                "title": title,
                "status_code": status,
                "loaded": True
            }
            
            # Add wait confirmation if selector was provided
            if wait_for:
                result["waited_for"] = wait_for
                
            logger.info(f"Navigation successful: {title} ({status})")
            return result
            
        except PlaywrightTimeoutError as e:
            error_msg = f"Navigation timeout after {timeout}s: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        except Exception as e:
            error_msg = f"Navigation failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def get_page_content(self, include_links: bool = False, 
                              selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract content from the current page.
        
        Args:
            include_links: Whether to include link URLs in the output
            selector: Optional CSS selector to extract specific content
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            page = await self.browser_manager.get_current_page()
            
            # Get basic page info
            title = await page.title()
            url = page.url
            
            # Extract content based on selector
            if selector:
                logger.info(f"Extracting content from selector: {selector}")
                elements = await page.query_selector_all(selector)
                
                if not elements:
                    return {
                        "success": False,
                        "error": f"No elements found matching selector: {selector}",
                        "url": url,
                        "title": title
                    }
                
                content_parts = []
                for element in elements:
                    text_content = await element.inner_text()
                    if text_content.strip():
                        content_parts.append(text_content.strip())
                
                content = "\n\n".join(content_parts)
                
            else:
                # Get full page content
                logger.info("Extracting full page content")
                content = await page.inner_text("body")
            
            # Process links if requested
            links = []
            if include_links:
                link_elements = await page.query_selector_all("a[href]")
                for link in link_elements:
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    
                    if href and text.strip():
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(url, href)
                        links.append({
                            "text": text.strip(),
                            "url": absolute_url
                        })
            
            # Clean and format content
            clean_content = extract_text_content(content)
            
            result = {
                "success": True,
                "url": url,
                "title": title,
                "content": clean_content,
                "content_length": len(clean_content),
                "selector_used": selector
            }
            
            if include_links:
                result["links"] = links
                result["link_count"] = len(links)
            
            logger.info(f"Content extracted: {len(clean_content)} characters")
            return result
            
        except Exception as e:
            error_msg = f"Content extraction failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "url": page.url if 'page' in locals() else None
            }
    
    async def click_element(self, selector: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Click on an element specified by CSS selector.
        
        Args:
            selector: CSS selector for the target element
            timeout: Timeout in seconds for finding the element
            
        Returns:
            Dictionary containing click result
        """
        try:
            page = await self.browser_manager.get_current_page()
            
            logger.info(f"Clicking element: {selector}")
            
            # Wait for element to be visible and enabled
            await page.wait_for_selector(selector, timeout=timeout * 1000)
            element = await page.query_selector(selector)
            
            if not element:
                raise RuntimeError(f"Element not found: {selector}")
            
            # Check if element is visible and enabled
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()
            
            if not is_visible:
                raise RuntimeError(f"Element is not visible: {selector}")
            
            if not is_enabled:
                raise RuntimeError(f"Element is not enabled: {selector}")
            
            # Perform the click
            await element.click()
            
            # Wait a moment for any page changes
            await asyncio.sleep(0.5)
            
            result = {
                "success": True,
                "selector": selector,
                "clicked": True,
                "final_url": page.url
            }
            
            logger.info(f"Element clicked successfully: {selector}")
            return result
            
        except PlaywrightTimeoutError:
            error_msg = f"Element not found within {timeout}s: {selector}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "selector": selector
            }
            
        except Exception as e:
            error_msg = f"Click failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "selector": selector
            }
    
    async def fill_form(self, fields: Dict[str, str], submit: bool = False) -> Dict[str, Any]:
        """
        Fill form fields with specified values.
        
        Args:
            fields: Dictionary mapping CSS selectors to values
            submit: Whether to submit the form after filling
            
        Returns:
            Dictionary containing form filling results
        """
        try:
            page = await self.browser_manager.get_current_page()
            
            logger.info(f"Filling form with {len(fields)} fields")
            
            filled_fields = []
            failed_fields = []
            
            # Fill each field
            for selector, value in fields.items():
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    element = await page.query_selector(selector)
                    
                    if not element:
                        failed_fields.append({
                            "selector": selector,
                            "error": "Element not found"
                        })
                        continue
                    
                    # Clear existing content and fill
                    await element.clear()
                    await element.fill(str(value))
                    
                    filled_fields.append({
                        "selector": selector,
                        "value": str(value)
                    })
                    
                    logger.info(f"Filled field: {selector}")
                    
                except Exception as field_error:
                    failed_fields.append({
                        "selector": selector,
                        "error": str(field_error)
                    })
                    logger.warning(f"Failed to fill field {selector}: {field_error}")
            
            result = {
                "success": len(filled_fields) > 0,
                "filled_count": len(filled_fields),
                "failed_count": len(failed_fields),
                "filled_fields": filled_fields,
                "failed_fields": failed_fields
            }
            
            # Submit form if requested
            if submit and filled_fields:
                try:
                    logger.info("Submitting form")
                    # Try to find and click submit button
                    submit_selectors = [
                        'input[type="submit"]',
                        'button[type="submit"]', 
                        'button:has-text("Submit")',
                        'button:has-text("Send")',
                        'button:has-text("Login")'
                    ]
                    
                    submitted = False
                    for submit_selector in submit_selectors:
                        submit_element = await page.query_selector(submit_selector)
                        if submit_element:
                            await submit_element.click()
                            submitted = True
                            break
                    
                    if not submitted:
                        # Try pressing Enter on the last filled field
                        if filled_fields:
                            last_selector = filled_fields[-1]["selector"]
                            await page.press(last_selector, "Enter")
                            submitted = True
                    
                    result["submitted"] = submitted
                    result["final_url"] = page.url
                    
                    if submitted:
                        # Wait for potential page changes
                        await asyncio.sleep(1)
                        logger.info("Form submitted successfully")
                    
                except Exception as submit_error:
                    result["submit_error"] = str(submit_error)
                    logger.warning(f"Form submission failed: {submit_error}")
            
            return result
            
        except Exception as e:
            error_msg = f"Form filling failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def take_screenshot(self, full_page: bool = False, 
                             selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot of the current page or specific element.
        
        Args:
            full_page: Whether to capture the full page height
            selector: Optional CSS selector for element screenshot
            
        Returns:
            Dictionary containing screenshot data and metadata
        """
        try:
            page = await self.browser_manager.get_current_page()
            
            logger.info(f"Taking screenshot - full_page: {full_page}, selector: {selector}")
            
            screenshot_options = {"type": "png"}
            
            if selector:
                # Screenshot specific element
                element = await page.query_selector(selector)
                if not element:
                    raise RuntimeError(f"Element not found for screenshot: {selector}")
                
                screenshot_bytes = await element.screenshot(**screenshot_options)
                screenshot_type = "element"
                
            else:
                # Screenshot full page or viewport
                screenshot_options["full_page"] = full_page
                screenshot_bytes = await page.screenshot(**screenshot_options)
                screenshot_type = "full_page" if full_page else "viewport"
            
            # Encode to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            result = {
                "success": True,
                "screenshot": screenshot_base64,
                "format": "png",
                "type": screenshot_type,
                "size_bytes": len(screenshot_bytes),
                "url": page.url,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            if selector:
                result["selector"] = selector
            
            logger.info(f"Screenshot captured: {len(screenshot_bytes)} bytes")
            return result
            
        except Exception as e:
            error_msg = f"Screenshot failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "selector": selector
            }
    
    async def execute_javascript(self, code: str, return_value: bool = True) -> Dict[str, Any]:
        """
        Execute JavaScript code in the browser context.
        
        Args:
            code: JavaScript code to execute
            return_value: Whether to return the execution result
            
        Returns:
            Dictionary containing execution result
        """
        try:
            page = await self.browser_manager.get_current_page()
            
            logger.info("Executing JavaScript code")
            
            # Execute the JavaScript
            if return_value:
                result = await page.evaluate(code)
                execution_result = {
                    "success": True,
                    "result": result,
                    "returned_value": True
                }
            else:
                await page.evaluate(code)
                execution_result = {
                    "success": True,
                    "executed": True,
                    "returned_value": False
                }
            
            execution_result["url"] = page.url
            
            logger.info("JavaScript executed successfully")
            return execution_result
            
        except Exception as e:
            error_msg = f"JavaScript execution failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "code": code[:100] + "..." if len(code) > 100 else code
            }
    
    async def get_page_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the current page.
        
        Returns:
            Dictionary containing detailed page information
        """
        try:
            page = await self.browser_manager.get_current_page()
            
            # Basic page info
            title = await page.title()
            url = page.url
            
            # Viewport info
            viewport = page.viewport_size
            
            # Count various elements
            link_count = len(await page.query_selector_all("a[href]"))
            form_count = len(await page.query_selector_all("form"))
            image_count = len(await page.query_selector_all("img"))
            input_count = len(await page.query_selector_all("input, textarea, select"))
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "viewport": viewport,
                "element_counts": {
                    "links": link_count,
                    "forms": form_count,
                    "images": image_count,
                    "inputs": input_count
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to get page info: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }