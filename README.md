# MATLAB MCP Server

**⚠️ ALPHA VERSION - Use at your own risk**

A Model Context Protocol (MCP) server that enables Claude Desktop to interact with your local MATLAB installation. This is an early alpha release - expect bugs and incomplete features.

## What This Does

Allows Claude Desktop to execute MATLAB code on your computer through the MCP protocol. Figures will pop up in MATLAB's GUI for you to interact with directly.

## Installation

**⚠️ IMPORTANT: Only the Windows installer is officially supported**

### Windows Installer (Only Supported Method)

1. **Download** the latest `matlab-mcp-server-setup-X.X.X.exe` from the releases

2. **Run the installer**:
   - Follow the installation wizard
   - Select your MATLAB installation folder when prompted
   - The installer will configure everything for you

3. **Configure Claude Desktop**:
   - The installer creates a `claude_config_example.json` file
   - Copy its contents to: `%APPDATA%\Claude\claude_desktop_config.json`
   - Restart Claude Desktop

4. **Test it**: Ask Claude to create a simple MATLAB plot

### Unsupported Installation Methods

Building from source or development installations are **not officially supported** and may not work correctly. Use the Windows installer.

## Requirements

**Tested Platform:**
- Windows (only supported OS)
- MATLAB R2025b (25.2.0.2998904)
- **⚠️ Other MATLAB versions are NOT tested and may not work**

**Required Software:**
- Local MATLAB R2025b installation
- Valid MATLAB license (standard license, no special features required)
- MATLAB Engine API for Python (installed via your MATLAB license)
- Claude Desktop

**Important:** You must install the MATLAB Engine API for Python from your own MATLAB installation. The installer cannot do this for you. This requires a valid MATLAB license.

## Configuration

After installing via the Windows installer, you'll have a `claude_config_example.json` file. The configuration should look like:

```json
{
  "mcpServers": {
    "matlab": {
      "command": "C:\\Program Files\\MATLAB MCP Server\\matlab-mcp-server.exe",
      "env": {
        "MATLAB_PATH": "C:\\Program Files\\MATLAB\\R2025b"
      }
    }
  }
}
```

Copy this to `%APPDATA%\Claude\claude_desktop_config.json` and restart Claude Desktop.

## What Works (Alpha)

Basic functionality:
- Execute MATLAB code
- View figures (they pop up in MATLAB GUI)
- Get workspace variables
- List workspace contents
- Clear workspace
- Export figures to files (if needed)
- Project management
- Automatic figure positioning on screen
- Script auto-archiving

## Known Issues

This is alpha software. Known issues:
- Only tested on Windows
- MATLAB Engine API compatibility warnings with Python 3.13
- Limited error handling
- No comprehensive testing yet
- May not work with all MATLAB versions
- Performance not optimized

## How to Use

Once configured, ask Claude Desktop things like:
- "Create a plot of sin(x) from 0 to 2π"
- "Solve this equation: x^2 + 2x + 1 = 0"
- "Show me what's in the MATLAB workspace"

Figures will appear in MATLAB GUI windows automatically positioned on your screen.

## Troubleshooting

If it doesn't work:
1. Make sure MATLAB is installed and the path in the config is correct
2. Restart Claude Desktop after configuration changes
3. Check Claude Desktop logs for errors
4. Try reinstalling via the Windows installer

## License

MIT License - see LICENSE file for details

## Disclaimer

This is alpha software provided as-is with no warranty. Use at your own risk. Not affiliated with MathWorks.
