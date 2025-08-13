#!/usr/bin/env python3
"""
Manual test of browser automation tools to demonstrate functionality
"""
import json
import subprocess
import sys

def send_mcp_request(method, params=None, request_id=1):
    """Send an MCP request and return the response"""
    if params is None:
        params = {}
    
    # Initialize the server
    init_msg = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "manual_test", "version": "1.0"}
        },
        "id": 0
    }
    
    initialized_msg = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    request_msg = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    
    # Prepare input
    input_data = "\n".join([
        json.dumps(init_msg),
        json.dumps(initialized_msg),
        json.dumps(request_msg)
    ]) + "\n"
    
    # Run the server
    try:
        result = subprocess.run(
            ["./start_mcp.sh"],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=30
        )
        
        # Parse responses
        lines = result.stdout.strip().split('\n')
        responses = [json.loads(line) for line in lines if line.strip()]
        
        # Return the last response (our request)
        return responses[-1] if responses else None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_navigation():
    """Test browser navigation"""
    print("🌐 Testing navigation to Google...")
    
    response = send_mcp_request("tools/call", {
        "name": "navigate_to",
        "arguments": {"url": "https://google.com"}
    }, 3)
    
    if response and "result" in response:
        result = response["result"]
        print(f"✅ Navigation successful!")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   Title: {result.get('title', 'N/A')}")
        return True
    else:
        print(f"❌ Navigation failed: {response}")
        return False

def test_screenshot():
    """Test screenshot capture"""
    print("📸 Testing screenshot capture...")
    
    response = send_mcp_request("tools/call", {
        "name": "take_screenshot",
        "arguments": {"full_page": False}
    }, 4)
    
    if response and "result" in response:
        result = response["result"]
        print(f"✅ Screenshot captured!")
        print(f"   File: {result.get('screenshot_path', 'N/A')}")
        return True
    else:
        print(f"❌ Screenshot failed: {response}")
        return False

def main():
    """Run manual tests of browser automation"""
    print("🧪 Manual Browser Automation Test")
    print("=" * 40)
    
    # Test tools list first
    print("📋 Testing tools list...")
    response = send_mcp_request("tools/list")
    
    if response and "result" in response:
        tools = response["result"]["tools"]
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
        print()
        
        # Run browser tests
        success = True
        success &= test_navigation()
        success &= test_screenshot()
        
        if success:
            print("\n🎉 All tests passed! Browser automation is working.")
        else:
            print("\n⚠️  Some tests failed. Check the output above.")
            
    else:
        print(f"❌ Failed to get tools list: {response}")
        sys.exit(1)

if __name__ == "__main__":
    main()