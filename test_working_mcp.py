#!/usr/bin/env python3
"""
Test the working MCP server to verify all functionality.
"""
import subprocess
import sys
import json
import time

def test_working_mcp():
    """Test the working MCP server"""
    print("Testing working MCP server...")
    
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
        # 3. Tools list request
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
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
        ], input=input_text, capture_output=True, text=True, timeout=10)
        
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
                    print(f"✅ Valid JSON response: {json.dumps(response, indent=2)}")
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {line} - Error: {e}")
        
        # Validate responses
        if len(responses) >= 2:
            init_response = responses[0]
            tools_response = responses[1]
            
            # Check initialize response
            if (init_response.get("jsonrpc") == "2.0" and 
                "result" in init_response and
                "capabilities" in init_response["result"]):
                print("✅ Initialize response is valid")
            else:
                print("❌ Initialize response is invalid")
                
            # Check tools response
            if (tools_response.get("jsonrpc") == "2.0" and 
                "result" in tools_response and
                "tools" in tools_response["result"]):
                print("✅ Tools response is valid")
                tools = tools_response["result"]["tools"]
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            else:
                print("❌ Tools response is invalid")
                
            return True
        else:
            print(f"❌ Expected 2+ responses, got {len(responses)}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Server timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_working_mcp()
    sys.exit(0 if success else 1)