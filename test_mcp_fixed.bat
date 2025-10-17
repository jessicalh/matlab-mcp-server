@echo off
echo Testing MATLAB MCP Server with MCP Inspector
echo ============================================
echo.

REM Set environment variables
set MATLAB_PATH=C:\Program Files\MATLAB\R2025b

echo Starting MCP Inspector...
echo When the interface opens, you should see:
echo   - Available tools listed
echo   - Ability to execute MATLAB code
echo   - Figures will pop up in MATLAB windows
echo.
echo Press Ctrl+C to stop when done testing
echo.

npx @modelcontextprotocol/inspector dist\matlab-mcp-server-v2\matlab-mcp-server.exe

pause