#!/usr/bin/env python3
"""MATLAB MCP Server - Main entry point for PyInstaller."""

import sys
import os

# Ensure stdout/stderr are not closed for PyInstaller
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    # Ensure streams are open
    if sys.stdout is None or sys.stdout.closed:
        sys.stdout = sys.stderr
    if sys.stdin is None or sys.stdin.closed:
        # Create a dummy stdin that returns EOF
        import io
        sys.stdin = io.StringIO('')

# Now import and run the server
if __name__ == "__main__":
    from matlab_mcp_server.server import main
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down MATLAB MCP Server...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)