"""
Utility Functions Module

This module provides utility functions for data processing, validation,
and formatting used throughout the browser MCP server. These functions
handle common tasks like HTML sanitization, URL validation, content
extraction, and error formatting.

Key Functions:
- HTML sanitization and cleaning
- URL validation and normalization  
- Text content extraction and formatting
- Screenshot processing and encoding
- Error response formatting
- Data type validation and conversion
"""

import base64
import html
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, urljoin
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: String to validate as URL
        
    Returns:
        True if valid URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
        
    try:
        parsed = urlparse(url.strip())
        return all([
            parsed.scheme in ('http', 'https', 'ftp', 'ftps'),
            parsed.netloc,
            # Basic domain validation
            '.' in parsed.netloc or parsed.netloc == 'localhost'
        ])
    except Exception:
        return False


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize and clean a URL.
    
    Args:
        url: URL to normalize
        base_url: Optional base URL for resolving relative URLs
        
    Returns:
        Normalized URL string
        
    Raises:
        ValueError: If URL cannot be normalized
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    # Handle relative URLs
    if base_url and not url.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
        url = urljoin(base_url, url)
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
        url = 'https://' + url
    
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL after normalization: {url}")
        
    return url


def sanitize_html(html_content: str, preserve_links: bool = False) -> str:
    """
    Sanitize HTML content by removing scripts and dangerous elements.
    
    Args:
        html_content: Raw HTML content to sanitize
        preserve_links: Whether to preserve link information
        
    Returns:
        Sanitized HTML content
    """
    if not html_content:
        return ""
    
    # Remove script tags and their content
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove style tags and their content
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove dangerous attributes
    dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout', 'onfocus', 'onblur']
    for attr in dangerous_attrs:
        html_content = re.sub(f'{attr}=["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
    
    # Extract link information if preserving
    if preserve_links:
        # This is a simple approach - a full implementation would use proper HTML parsing
        link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>'
        links = re.findall(link_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        # Replace links with formatted text
        def replace_link(match):
            href = match.group(1)
            text = match.group(2)
            return f"{text} [{href}]"
        
        html_content = re.sub(link_pattern, replace_link, html_content, flags=re.DOTALL | re.IGNORECASE)
    
    return html_content


def extract_text_content(content: str, max_length: Optional[int] = None) -> str:
    """
    Extract and clean text content from HTML or raw text.
    
    Args:
        content: Content to clean and extract text from
        max_length: Optional maximum length to truncate to
        
    Returns:
        Clean text content
    """
    if not content:
        return ""
    
    # Decode HTML entities
    content = html.unescape(content)
    
    # Remove extra whitespace and normalize line breaks
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'\n\s*\n', '\n\n', content)
    
    # Remove leading/trailing whitespace
    content = content.strip()
    
    # Truncate if max_length specified
    if max_length and len(content) > max_length:
        content = content[:max_length] + "..."
        
    return content


def format_error_response(error_message: str, tool_name: str = None, 
                         arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Format a standardized MCP-compliant error response.
    
    Args:
        error_message: Error message to include
        tool_name: Name of the tool that failed
        arguments: Arguments that were passed to the tool
        
    Returns:
        MCP-compliant error response dictionary
    """
    # Format error message for tool context
    if tool_name:
        formatted_message = f"Error in tool '{tool_name}': {error_message}"
    else:
        formatted_message = error_message
    
    # Return MCP-compliant error response format
    return {
        "content": [
            {
                "type": "text",
                "text": formatted_message
            }
        ],
        "isError": True
    }


def encode_image_base64(image_bytes: bytes, format: str = "PNG") -> str:
    """
    Encode image bytes to base64 string.
    
    Args:
        image_bytes: Raw image bytes
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        Base64 encoded image string
    """
    return base64.b64encode(image_bytes).decode('utf-8')


def decode_base64_image(base64_string: str) -> bytes:
    """
    Decode base64 string to image bytes.
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        Raw image bytes
        
    Raises:
        ValueError: If base64 string is invalid
    """
    try:
        return base64.b64decode(base64_string)
    except Exception as e:
        raise ValueError(f"Invalid base64 string: {str(e)}")


def resize_image(image_bytes: bytes, max_width: int = 1024, 
                max_height: int = 768) -> bytes:
    """
    Resize image to fit within specified dimensions.
    
    Args:
        image_bytes: Raw image bytes
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        
    Returns:
        Resized image bytes
        
    Raises:
        ImportError: If PIL is not available
        ValueError: If image cannot be processed
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL (Pillow) is required for image resizing")
    
    try:
        # Open image from bytes
        image = Image.open(BytesIO(image_bytes))
        
        # Calculate new size maintaining aspect ratio
        original_width, original_height = image.size
        
        if original_width <= max_width and original_height <= max_height:
            return image_bytes  # No resize needed
        
        # Calculate scaling factor
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale_factor = min(width_ratio, height_ratio)
        
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert back to bytes
        output = BytesIO()
        resized_image.save(output, format=image.format or 'PNG')
        
        return output.getvalue()
        
    except Exception as e:
        raise ValueError(f"Failed to resize image: {str(e)}")


def validate_css_selector(selector: str) -> bool:
    """
    Validate if a string is a potentially valid CSS selector.
    
    Args:
        selector: CSS selector string to validate
        
    Returns:
        True if selector appears valid, False otherwise
    """
    if not selector or not isinstance(selector, str):
        return False
    
    # Basic validation - check for obvious invalid patterns
    invalid_patterns = [
        r'^\s*$',  # Empty or whitespace only
        r'[<>]',   # HTML-like characters
        r'javascript:',  # JavaScript protocol
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, selector, re.IGNORECASE):
            return False
    
    # Must contain some valid CSS selector characters
    valid_chars = re.search(r'[a-zA-Z0-9#.\-_\[\]:()]', selector)
    
    return bool(valid_chars)


def clean_filename(filename: str, max_length: int = 255) -> str:
    """
    Clean a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        max_length: Maximum length for the filename
        
    Returns:
        Cleaned filename safe for filesystem use
    """
    if not filename:
        return "untitled"
    
    # Remove or replace invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    cleaned = re.sub(r'\s+', '_', cleaned)  # Replace spaces with underscores
    cleaned = cleaned.strip('.')  # Remove leading/trailing dots
    
    # Truncate if too long
    if len(cleaned) > max_length:
        name, ext = cleaned.rsplit('.', 1) if '.' in cleaned else (cleaned, '')
        available_length = max_length - len(ext) - 1 if ext else max_length
        cleaned = name[:available_length] + ('.' + ext if ext else '')
    
    return cleaned or "untitled"


def parse_viewport_size(viewport_string: str) -> Dict[str, int]:
    """
    Parse viewport size from string format.
    
    Args:
        viewport_string: String in format "1280x720" or "1280,720"
        
    Returns:
        Dictionary with width and height keys
        
    Raises:
        ValueError: If format is invalid
    """
    if not viewport_string:
        raise ValueError("Viewport string cannot be empty")
    
    # Try different separators
    for separator in ['x', 'X', ',', ' ']:
        if separator in viewport_string:
            parts = viewport_string.split(separator)
            if len(parts) == 2:
                try:
                    width = int(parts[0].strip())
                    height = int(parts[1].strip())
                    
                    if width > 0 and height > 0:
                        return {"width": width, "height": height}
                except ValueError:
                    continue
    
    raise ValueError(f"Invalid viewport format: {viewport_string}")


def take_screenshot(screenshot_bytes: bytes, filename: str = None) -> str:
    """
    Save screenshot bytes to file and return the path.
    
    Args:
        screenshot_bytes: Raw screenshot bytes
        filename: Optional filename, auto-generated if not provided
        
    Returns:
        Path to saved screenshot file
    """
    import tempfile
    import os
    from datetime import datetime
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
    else:
        filename = clean_filename(filename)
    
    # Create temporary file
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    # Write screenshot to file
    with open(filepath, 'wb') as f:
        f.write(screenshot_bytes)
    
    logger.info(f"Screenshot saved to: {filepath}")
    return filepath


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append when truncating
        
    Returns:
        Truncated text with suffix if needed
    """
    if not text or len(text) <= max_length:
        return text
    
    # Account for suffix length
    truncate_length = max_length - len(suffix)
    if truncate_length < 0:
        truncate_length = max_length
        suffix = ""
    
    return text[:truncate_length] + suffix