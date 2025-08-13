#!/usr/bin/env python3
"""
Test the MCP server with proper JSON-RPC commands to identify protocol violations.
"""
import subprocess
import sys
import json
import time
import signal

def test_mcp_protocol():
    """Test the MCP server protocol compliance"""
    print("Testing MCP server JSON-RPC protocol compliance...")
    
    # Start the server in a subprocess
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "src.server"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
           text=True, bufsize=0)
        
        # Give it a moment to start
        time.sleep(1)
        
        # Check if it's still running
        if process.poll() is not None:
            print("❌ Server exited immediately")
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
        # Test 1: Initialize request
        print("\n🔍 Testing initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Test 2: Tools list request
        print("🔍 Testing tools/list request...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_request) + '\n')
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Try to read any output
        try:
            stdout_data = ""
            stderr_data = ""
            
            # Read available stdout
            while True:
                try:
                    char = process.stdout.read(1)
                    if not char:
                        break
                    stdout_data += char
                    if len(stdout_data) > 1000:  # Prevent runaway
                        break
                except:
                    break
            
            # Read available stderr  
            while True:
                try:
                    char = process.stderr.read(1)
                    if not char:
                        break
                    stderr_data += char
                    if len(stderr_data) > 1000:  # Prevent runaway
                        break
                except:
                    break
                    
            print(f"\n📤 STDOUT Response:\n{stdout_data}")
            print(f"\n📤 STDERR Response:\n{stderr_data}")
            
            # Analyze responses
            if stdout_data:
                print("\n✅ Server produced output on stdout")
                # Try to parse as JSON-RPC
                try:
                    lines = stdout_data.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            response = json.loads(line)
                            print(f"  📝 Parsed JSON response: {response}")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Invalid JSON in stdout: {e}")
            else:
                print("❌ No output on stdout")
                
            if stderr_data:
                print("✅ Server logs properly directed to stderr")
            
        except Exception as e:
            print(f"❌ Error reading server output: {e}")
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False
    finally:
        # Clean up
        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass
                
    return True

if __name__ == "__main__":
    success = test_mcp_protocol()
    sys.exit(0 if success else 1)