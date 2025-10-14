"""PyInstaller hook for MCP SDK."""

from PyInstaller.utils.hooks import collect_all

# Collect all MCP package data, binaries, and hidden imports
datas, binaries, hiddenimports = collect_all('mcp')

# Add specific hidden imports
hiddenimports += [
    'mcp.server',
    'mcp.server.stdio',
    'mcp.types',
]
