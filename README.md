# Browser MCP Server

A **Model Context Protocol (MCP)** server that provides comprehensive browser automation capabilities using [Playwright](https://playwright.dev/). This server enables AI assistants to interact with web pages through standardized MCP tools for navigation, content extraction, form filling, and screenshot capture.

## 🚀 Features

### Core Browser Operations
- **Navigate to URLs** with smart waiting strategies
- **Extract page content** with customizable selectors  
- **Take screenshots** (full page, viewport, or specific elements)
- **Execute JavaScript** with result capture
- **Click elements** by CSS selectors
- **Fill forms** automatically with validation

### Advanced Capabilities
- **Multi-browser support** (Chromium, Firefox, WebKit)
- **Request interception** and monitoring
- **Viewport customization** and responsive testing
- **Link extraction** and URL processing
- **Error handling** with detailed responses
- **Resource management** and cleanup

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Node.js (for Playwright browser installation)

### Install from Source
```bash
# Clone the repository
git clone <repository-url>
cd claude-browser-mcp

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install
```

### Install from PyPI (when available)
```bash
pip install claude-browser-mcp
playwright install
```

## 🛠 Usage

### As MCP Server
Start the server with stdio transport:
```bash
browser-mcp
# or
python -m src.server
```

### Configuration
Configure the browser through environment variables:
```bash
export BROWSER_HEADLESS=true          # Run in headless mode
export BROWSER_TYPE=chromium          # Browser type (chromium/firefox/webkit)
export BROWSER_TIMEOUT=30000          # Default timeout in milliseconds
```

### MCP Client Integration
Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "browser-automation": {
      "command": "browser-mcp",
      "args": []
    }
  }
}
```

## 🔧 Available Tools

### `navigate_to`
Navigate to a specified URL with optional waiting.
```json
{
  "name": "navigate_to",
  "arguments": {
    "url": "https://example.com",
    "wait_for": "selector", 
    "timeout": 30
  }
}
```

### `get_page_content`
Extract text content from the current page.
```json
{
  "name": "get_page_content", 
  "arguments": {
    "include_links": true,
    "selector": ".main-content"
  }
}
```

### `click_element`
Click on elements by CSS selector.
```json
{
  "name": "click_element",
  "arguments": {
    "selector": "button#submit",
    "timeout": 10
  }
}
```

### `fill_form`
Fill form fields with data.
```json
{
  "name": "fill_form",
  "arguments": {
    "fields": {
      "#email": "user@example.com",
      "#password": "secretpass"
    },
    "submit": true
  }
}
```

### `take_screenshot`
Capture page screenshots.
```json
{
  "name": "take_screenshot",
  "arguments": {
    "full_page": true,
    "selector": ".dashboard"
  }
}
```

### `execute_javascript`
Run JavaScript in the browser context.
```json
{
  "name": "execute_javascript", 
  "arguments": {
    "code": "document.title",
    "return_value": true
  }
}
```

## 📁 Project Structure

```
claude-browser-mcp/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── server.py            # MCP server implementation
│   ├── browser.py           # Browser management
│   ├── actions.py           # High-level browser actions
│   └── utils.py             # Utility functions
├── requirements.txt         # Python dependencies
├── setup.py                 # Package configuration
└── README.md               # This file
```

## 🏗 Architecture

### Server (`server.py`)
- MCP server implementation with tool registration
- Request routing and response formatting
- Error handling and logging
- Async tool execution

### Browser Manager (`browser.py`)  
- Playwright browser lifecycle management
- Context creation and configuration
- Resource cleanup and recovery
- Multi-browser support

### Actions (`actions.py`)
- High-level browser automation methods
- Content extraction and processing
- Form interaction and validation
- Screenshot and JavaScript execution

### Utils (`utils.py`)
- HTML sanitization and cleaning
- URL validation and normalization
- Image processing and encoding
- Data formatting utilities

## 🔒 Security Considerations

- **HTML sanitization** removes dangerous scripts and attributes
- **URL validation** prevents malicious redirects
- **Input validation** for all user-provided data
- **Resource limits** prevent excessive memory usage
- **Timeout controls** prevent hanging operations

## 🚨 Error Handling

The server provides detailed error responses with:
- **Error categorization** (timeout, validation, execution)
- **Context information** (URL, selector, arguments)
- **Recovery suggestions** where applicable
- **Logging** for debugging and monitoring

## 📊 Response Format

All tools return standardized JSON responses:
```json
{
  "success": true,
  "url": "https://example.com",
  "title": "Page Title",
  "data": "...",
  "metadata": {
    "timestamp": "...",
    "execution_time": "..."
  }
}
```

Error responses include:
```json
{
  "success": false,
  "error": "Detailed error message",
  "tool": "tool_name",
  "arguments": {...},
  "timestamp": "..."
}
```

## 🛡 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BROWSER_HEADLESS` | `true` | Run browser in headless mode |
| `BROWSER_TYPE` | `chromium` | Browser engine to use |
| `BROWSER_TIMEOUT` | `30000` | Default timeout (ms) |

## 🤝 Development

### Setting up Development Environment
```bash
# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/

# Format code
black src/

# Type checking
mypy src/
```

### Adding New Tools
1. Define tool schema in `server.py`
2. Implement action method in `actions.py`
3. Add utility functions in `utils.py`
4. Update documentation and tests

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for browser automation
- [MCP](https://modelcontextprotocol.io/) for the protocol specification
- [Anthropic](https://anthropic.com/) for Claude and MCP development

## 📞 Support

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: See inline code documentation
- **Community**: Join MCP community discussions

---

**Note**: This is a foundational implementation. Additional features like request interception, advanced form handling, and performance optimizations can be added based on specific use cases.