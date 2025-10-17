# PyInstaller Executable Debugging Notes

## Issue
The PyInstaller executable hangs when run from Claude Desktop but works when tested directly.

## Key Findings

### 1. The Hang Location
- Executable hangs inside `app.run()` in the MCP server event loop
- Works fine when tested with a single request that closes stdin
- Hangs when Claude Desktop keeps the connection open for bidirectional communication

### 2. What We've Tested

#### Logging Issues
- ✅ Removed stderr logging in frozen mode (was interfering with MCP protocol)
- ✅ Added NullHandler when no log handlers configured
- ✅ Created debug log file (`matlab_mcp_debug.log`) for diagnostics

#### Stream Handling
- ✅ Tried not modifying stdin/stdout/stderr
- ✅ Added clean exit with `os._exit(0)` to avoid I/O errors
- ❌ ProactorEventLoop - still hangs
- ❌ SelectorEventLoop - still hangs

#### Debug Output Shows
```
Starting asyncio event loop...
Set Windows SelectorEventLoopPolicy for better stdio
main() called at 2025-10-17 17:44:10.585719
About to enter stdio_server context...
stdio_server context established: read=MemoryObjectReceiveStream(...), write=MemoryObjectSendStream(...)
About to call app.run()...
[HANGS HERE - never reaches "app.run() completed"]
```

## Working Alternative
Running directly with Python works:
```json
"matlab": {
  "command": "python",
  "args": ["-m", "src.matlab_mcp_server.server"],
  "cwd": "C:\\projects\\matlabserver",
  "env": {
    "MATLAB_PATH": "C:\\Program Files\\MATLAB\\R2025b",
    "MATLAB_WORKSPACE_DIR": "C:\\projects\\matlabserver\\matlab_workspace"
  }
}
```

## Hypothesis
The issue is likely in how the MCP library's `stdio_server()` context manager handles streams in a frozen Windows executable when the streams remain open for bidirectional communication (as Claude Desktop does) vs. closing after a single message (as our tests do).

## Next Steps to Investigate
1. Compare with earlier working version to see what changed
2. Look at how stdio_server() is implemented in the MCP library
3. Consider if we need custom stream handling for frozen Windows executables
4. Check if older PyInstaller version or different freeze options would help

## Files Modified
- `src/matlab_mcp_server/main.py` - Added debug logging and event loop configuration
- `src/matlab_mcp_server/server.py` - Fixed logging for frozen mode, added diagnostics
- `matlab-mcp-server.spec` - Updated to use main.py entry point