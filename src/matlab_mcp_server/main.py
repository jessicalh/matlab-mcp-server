#!/usr/bin/env python3
"""MATLAB MCP Server - Main entry point for PyInstaller."""

import sys
import os
import traceback
from datetime import datetime

# Create a debug log file for PyInstaller issues
debug_log = None
if getattr(sys, 'frozen', False):
    try:
        debug_log_path = os.path.join(os.path.dirname(sys.executable), 'matlab_mcp_debug.log')
        debug_log = open(debug_log_path, 'a')
        debug_log.write(f"\n\n=== MATLAB MCP Server Started at {datetime.now()} ===\n")
        debug_log.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
        debug_log.write(f"Executable: {sys.executable}\n")
        debug_log.write(f"Python: {sys.version}\n")
        debug_log.write(f"CWD: {os.getcwd()}\n")
        debug_log.flush()
    except Exception as e:
        # If we can't create debug log, continue anyway
        pass

try:
    # Ensure stdout/stderr are not closed for PyInstaller
    if getattr(sys, 'frozen', False):
        if debug_log:
            debug_log.write(f"Checking streams...\n")
            debug_log.write(f"stdin: {sys.stdin}\n")
            debug_log.write(f"stdout: {sys.stdout}\n")
            debug_log.write(f"stderr: {sys.stderr}\n")
            debug_log.flush()

        # Running as PyInstaller executable
        # Don't touch stdin/stdout/stderr - let MCP handle them
        pass

    # Now import and run the server
    if __name__ == "__main__":
        if debug_log:
            debug_log.write("Importing server module...\n")
            debug_log.flush()

        from matlab_mcp_server.server import main
        import asyncio

        if debug_log:
            debug_log.write("Starting asyncio event loop...\n")
            debug_log.flush()

        try:
            # Use different event loop policy for Windows frozen executables
            if sys.platform == 'win32' and getattr(sys, 'frozen', False):
                # Use WindowsSelectorEventLoopPolicy for better stdio handling
                # ProactorEventLoop has issues with stdin/stdout in some cases
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                if debug_log:
                    debug_log.write("Set Windows SelectorEventLoopPolicy for better stdio\n")
                    debug_log.flush()

            asyncio.run(main())
        except KeyboardInterrupt:
            if debug_log:
                debug_log.write("Keyboard interrupt received\n")
                debug_log.flush()
            print("\nShutting down MATLAB MCP Server...", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            if debug_log:
                debug_log.write(f"Fatal error: {e}\n")
                debug_log.write(traceback.format_exc())
                debug_log.flush()
            print(f"Fatal error: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)

except Exception as e:
    if debug_log:
        debug_log.write(f"Top-level exception: {e}\n")
        debug_log.write(traceback.format_exc())
        debug_log.flush()
    print(f"Startup error: {e}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)
finally:
    if debug_log:
        debug_log.write("=== MATLAB MCP Server Exiting ===\n")
        debug_log.close()

    # Suppress the "I/O operation on closed file" error on exit
    if getattr(sys, 'frozen', False):
        try:
            sys.stderr.close()
            sys.stdout.close()
            sys.stdin.close()
        except:
            pass
        # Exit cleanly
        os._exit(0)