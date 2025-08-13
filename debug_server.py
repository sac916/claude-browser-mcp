#!/usr/bin/env python3
"""Debug the MCP server tools registration"""

import asyncio
import sys
from src.server import app, handle_list_tools

async def test_server():
    """Test server tools"""
    try:
        print("Testing handle_list_tools...")
        tools = await handle_list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        print("\n✅ MCP Server tools are properly defined")
        return True
        
    except Exception as e:
        print(f"❌ Error testing tools: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)