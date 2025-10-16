@echo off
REM Simple MCP Inspector test for MATLAB MCP Server

echo ============================================
echo MATLAB MCP Server - Quick Test
echo ============================================
echo.

set MATLAB_PATH=C:\Program Files\MATLAB\R2025b
set EXE_PATH=C:\projects\matlabserver\dist\matlab-mcp-server\matlab-mcp-server.exe

echo Testing server startup and tool listing...
echo.
echo This will open MCP Inspector in interactive mode.
echo You can manually test the tools in the web UI.
echo.
echo Press Ctrl+C to exit when done.
echo.

pause

npx @modelcontextprotocol/inspector "%EXE_PATH%"
