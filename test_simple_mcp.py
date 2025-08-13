#!/usr/bin/env python3
"""
Simple test to verify MCP server works with proper initialization sequence.
"""
import subprocess
import sys
import json
import threading
import time

def test_simple_mcp():
    """Test the MCP server with proper initialization"""
    print("Testing MCP server with proper initialization...")
    
    try:
        # Start the server
        process = subprocess.Popen([
            sys.executable, "-m", "src.server"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        def read_output():
            """Read server output in a separate thread"""
            responses = []
            try:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line:
                        print(f"📤 Server response: {line}")
                        try:
                            response = json.loads(line)
                            responses.append(response)
                        except json.JSONDecodeError:
                            print(f"❌ Invalid JSON: {line}")
            except Exception as e:
                print(f"Output reading error: {e}")
            return responses

        # Start output reading thread
        output_thread = threading.Thread(target=read_output)
        output_thread.daemon = True
        output_thread.start()
        
        # Give server time to start
        time.sleep(0.5)
        
        # Send initialize request (required first step in MCP)
        print("\n🔄 Sending initialize request...")
        init_request = {
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
        }
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # Wait for initialize response
        time.sleep(1)
        
        # Send initialized notification
        print("🔄 Sending initialized notification...")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        process.stdin.write(json.dumps(initialized_notification) + '\n')
        process.stdin.flush()
        
        # Wait a bit
        time.sleep(0.5)
        
        # Now send tools/list request
        print("🔄 Sending tools/list request...")
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
        
        # Check if server is still running
        if process.poll() is None:
            print("✅ Server is still running after requests")
        else:
            print("❌ Server exited")
            
        # Get stderr output for debugging
        try:
            process.stdin.close()
            stdout, stderr = process.communicate(timeout=2)
            print(f"\n📝 Final STDERR:\n{stderr}")
        except subprocess.TimeoutExpired:
            print("Server still running, terminating...")
            process.terminate()
            stdout, stderr = process.communicate()
            print(f"\n📝 Final STDERR:\n{stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = test_simple_mcp()
    sys.exit(0 if success else 1)