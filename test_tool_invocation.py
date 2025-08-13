#!/usr/bin/env python3
"""
Test tool invocation on the MCP server.
"""
import subprocess
import sys
import json

def test_tool_invocation():
    """Test tool invocation and error handling"""
    print("Testing MCP server tool invocation...")
    
    # Create input sequence for the server
    input_sequence = [
        # 1. Initialize request
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        },
        # 2. Initialized notification
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        },
        # 3. Test invalid tool call (should return error properly)
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "invalid_tool",
                "arguments": {}
            }
        },
        # 4. Test valid tool call with invalid arguments
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "navigate_to",
                "arguments": {}  # Missing required 'url' parameter
            }
        }
    ]
    
    # Convert to input string
    input_text = ""
    for msg in input_sequence:
        input_text += json.dumps(msg) + "\n"
    
    try:
        # Run the server with the input
        result = subprocess.run([
            sys.executable, "-m", "src.server"
        ], input=input_text, capture_output=True, text=True, timeout=15)
        
        print(f"📤 Server STDOUT:\n{result.stdout}")
        print(f"📤 Server STDERR:\n{result.stderr}")
        
        # Parse the JSON responses
        stdout_lines = result.stdout.strip().split('\n')
        responses = []
        
        for line in stdout_lines:
            if line.strip():
                try:
                    response = json.loads(line)
                    responses.append(response)
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {line} - Error: {e}")
        
        print(f"\n📊 Total responses: {len(responses)}")
        
        # Check each response
        for i, response in enumerate(responses):
            print(f"\n📝 Response {i+1}: {json.dumps(response, indent=2)}")
            
            # Validate JSON-RPC structure
            if response.get("jsonrpc") == "2.0":
                print(f"  ✅ Valid JSON-RPC 2.0 format")
            else:
                print(f"  ❌ Invalid JSON-RPC format")
                
            # Check for proper error handling
            if "result" in response:
                result_data = response["result"]
                if "content" in result_data:
                    content = result_data["content"]
                    if content and len(content) > 0:
                        print(f"  ✅ Has content response")
                        # Check if this is an error response
                        if result_data.get("isError"):
                            print(f"  ✅ Properly marked as error response")
                        else:
                            print(f"  ℹ️  Success response")
                    else:
                        print(f"  ❌ Empty content in response")
                else:
                    print(f"  ℹ️  Non-tool response (initialization/etc)")
            elif "error" in response:
                print(f"  ✅ Has error response: {response['error']}")
            else:
                print(f"  ❌ Response has neither result nor error")
                
        return len(responses) > 0
        
    except subprocess.TimeoutExpired:
        print("❌ Server timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_tool_invocation()
    sys.exit(0 if success else 1)