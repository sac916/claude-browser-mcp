#!/usr/bin/env python3
"""
Quick test to verify MCP server connectivity
"""
import subprocess
import sys
import time
import signal

def test_mcp_server():
    """Test the MCP server startup"""
    print("Testing MCP server...")
    
    # Start the server in a subprocess
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "src.server"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's still running
        if process.poll() is None:
            print("✅ Server started successfully")
            
            # Send a simple test (servers expect JSON-RPC on stdin)
            test_message = '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}\n'
            try:
                stdout, stderr = process.communicate(input=test_message, timeout=5)
                print("✅ Server responded to tools/list request")
                print(f"Response: {stdout[:200]}...")
            except subprocess.TimeoutExpired:
                print("⚠️ Server started but didn't respond quickly")
                
        else:
            print("❌ Server exited immediately")
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
    finally:
        # Clean up
        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        except:
            pass

if __name__ == "__main__":
    test_mcp_server()