#!/usr/bin/env python3
"""
Test the startup script functionality
"""
import subprocess
import sys
import json
import time

def test_startup_script():
    """Test the MCP server startup script"""
    print("🧪 Testing MCP server startup script...")
    
    # Test with the startup script
    input_sequence = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        },
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
    ]
    
    input_text = "\n".join([json.dumps(msg) for msg in input_sequence]) + "\n"
    
    try:
        result = subprocess.run([
            "python3", "/home/gmitch/claude-browser-mcp/start_mcp_server.py"
        ], input=input_text, capture_output=True, text=True, timeout=15)
        
        print(f"📤 Exit code: {result.returncode}")
        print(f"📤 STDOUT:\n{result.stdout}")
        print(f"📤 STDERR:\n{result.stderr}")
        
        # Parse responses
        responses = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {line}")
                    
        if len(responses) >= 2:
            print(f"✅ Startup script works! Got {len(responses)} responses")
            return True
        else:
            print(f"❌ Expected responses, got {len(responses)}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Startup script timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing startup script: {e}")
        return False

if __name__ == "__main__":
    success = test_startup_script()
    sys.exit(0 if success else 1)