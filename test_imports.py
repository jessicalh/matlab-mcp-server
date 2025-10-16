#!/usr/bin/env python3
"""Test imports for MATLAB MCP Server."""

try:
    print("Testing imports...")

    print("1. Testing dotenv...")
    from dotenv import load_dotenv
    print("   [OK] dotenv")

    print("2. Testing matlab...")
    import matlab.engine
    print("   [OK] matlab.engine")

    print("3. Testing mcp...")
    from mcp.server import Server
    print("   [OK] mcp")

    print("\n[SUCCESS] All imports successful!")

except Exception as e:
    print(f"\n[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
