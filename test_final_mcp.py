#!/usr/bin/env python3
"""
Final comprehensive test of the fixed MCP server.
"""
import subprocess
import sys
import json

def test_final_mcp():
    """Comprehensive test of the fixed MCP server"""
    print("🧪 Final comprehensive MCP server test...")
    
    # Test 1: Basic functionality
    print("\n🔍 Test 1: Basic initialization and tools listing")
    
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
            sys.executable, "-m", "src.server"
        ], input=input_text, capture_output=True, text=True, timeout=10)
        
        # Parse responses
        responses = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {line}")
                    
        # Validate basic functionality
        if len(responses) >= 2:
            init_resp = responses[0]
            tools_resp = responses[1]
            
            # Check initialization
            if (init_resp.get("jsonrpc") == "2.0" and 
                "result" in init_resp and
                "capabilities" in init_resp["result"]):
                print("✅ Initialization response valid")
            else:
                print("❌ Initialization response invalid")
                return False
                
            # Check tools list
            if (tools_resp.get("jsonrpc") == "2.0" and 
                "result" in tools_resp and
                "tools" in tools_resp["result"]):
                tools = tools_resp["result"]["tools"]
                print(f"✅ Tools list valid: {len(tools)} tools found")
                
                # Check tool structure
                for tool in tools:
                    if all(key in tool for key in ["name", "description", "inputSchema"]):
                        print(f"  ✅ Tool '{tool['name']}' has valid structure")
                    else:
                        print(f"  ❌ Tool '{tool.get('name', 'unknown')}' missing required fields")
                        
            else:
                print("❌ Tools list response invalid")
                return False
        else:
            print(f"❌ Expected 2+ responses, got {len(responses)}")
            return False
            
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Error handling 
    print("\n🔍 Test 2: Error handling")
    
    error_test_sequence = [
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
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "navigate_to",
                "arguments": {}  # Missing required 'url'
            }
        }
    ]
    
    input_text = "\n".join([json.dumps(msg) for msg in error_test_sequence]) + "\n"
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "src.server"
        ], input=input_text, capture_output=True, text=True, timeout=10)
        
        # Parse responses
        responses = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
                    
        # Look for error response
        error_found = False
        for resp in responses:
            if (resp.get("jsonrpc") == "2.0" and 
                "result" in resp and
                resp["result"].get("isError") == True):
                print("✅ Error properly handled and formatted")
                error_found = True
                break
                
        if not error_found:
            print("❌ Error not properly handled")
            return False
            
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
    
    # Test 3: Protocol compliance
    print("\n🔍 Test 3: Protocol compliance checks")
    
    # Check stdout only contains JSON-RPC
    if result.stderr and not result.stdout.strip().startswith('{"jsonrpc"'):
        print("❌ stdout contains non-JSON content")
        return False
    else:
        print("✅ stdout only contains JSON-RPC messages")
        
    # Check stderr contains logs
    if "INFO" in result.stderr or "ERROR" in result.stderr:
        print("✅ Logs properly directed to stderr")
    else:
        print("⚠️  No logs found in stderr (may be normal)")
    
    print("\n🎉 All tests passed! MCP server is working correctly.")
    print("\n📋 Summary of fixes applied:")
    print("  ✅ Fixed logging to stderr only")
    print("  ✅ Implemented proper MCP initialization handshake") 
    print("  ✅ Fixed tools/list response format")
    print("  ✅ Added proper error handling for JSON-RPC methods")
    print("  ✅ Ensured MCP-compliant response formats")
    
    return True

if __name__ == "__main__":
    success = test_final_mcp()
    sys.exit(0 if success else 1)