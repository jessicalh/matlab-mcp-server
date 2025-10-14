# MATLAB MCP Server

A Model Context Protocol (MCP) server that provides comprehensive integration with local MATLAB installations. Enables Claude Desktop and other MCP clients to execute MATLAB code with full debugging output capture and multi-format export capabilities.

## Features

- **Full Output Capture**: Captures all MATLAB console output, warnings, errors, and debugging information
- **Multi-Format Export**: Export figures and results to PNG, SVG, PDF, LaTeX, or text
- **Workspace Management**: Interact with MATLAB workspace variables
- **Persistent Session**: Maintains a single MATLAB session for fast execution
- **No Web Server Required**: Uses MATLAB Engine API - works with standard MATLAB license

## Requirements

- Python 3.11 (required for MATLAB Engine API compatibility)
- Local MATLAB installation (R2020b or later recommended)
- Standard MATLAB license (no web server license needed)

## Installation

### Option 1: Windows Installer (Recommended for Windows)

1. **Download** the latest `matlab-mcp-server-setup-X.X.X.exe` from the releases page

2. **Run the installer**:
   - The installer will guide you through the setup process
   - You'll be prompted to select your MATLAB installation folder
   - The installer will automatically configure the server

3. **Configure Claude Desktop**:
   - The installer will create a `claude_config_example.json` file
   - Copy its contents to: `%APPDATA%\Claude\claude_desktop_config.json`
   - Restart Claude Desktop

4. **Done!** The MATLAB MCP Server will be available in Claude Desktop

### Option 2: Build from Source

#### Prerequisites
- Python 3.11
- MATLAB installation (R2020b or later)
- Git

#### Build Steps

**Windows:**
```batch
# Clone repository
git clone <your-repo-url>
cd matlab-mcp-server

# Set MATLAB path
set MATLAB_PATH=C:\Program Files\MATLAB\R2024b

# Run build script
build.bat
```

**macOS/Linux:**
```bash
# Clone repository
git clone <your-repo-url>
cd matlab-mcp-server

# Set MATLAB path
export MATLAB_PATH=/Applications/MATLAB_R2024b.app

# Run build script
./build.sh
```

The build script will:
1. Install Python dependencies
2. Install MATLAB Engine API for Python
3. Build the executable with PyInstaller
4. (Windows only) Create an installer with Inno Setup

#### Output Files
- **Executable**: `dist/matlab-mcp-server/matlab-mcp-server.exe` (Windows) or `dist/matlab-mcp-server/matlab-mcp-server` (macOS/Linux)
- **Installer** (Windows only): `dist/installer/matlab-mcp-server-setup-X.X.X.exe`

### Option 3: Development Installation

For development or if you prefer not to use the installer:

1. **Install Python 3.11** (if not already installed)

2. **Clone this repository**:
   ```bash
   git clone <your-repo-url>
   cd matlab-mcp-server
   ```

3. **Create virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -e .
   ```

5. **Install MATLAB Engine API for Python**:
   ```bash
   # Navigate to your MATLAB installation's Python engine directory
   # macOS/Linux:
   cd /Applications/MATLAB_R2024b.app/extern/engines/python
   # Windows:
   cd "C:\Program Files\MATLAB\R2024b\extern\engines\python"

   # Install the engine
   python setup.py install
   ```

6. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your MATLAB path
   ```

## Configuration

### For Claude Desktop

The configuration depends on your installation method:

#### If using Windows Installer:
The installer creates a `claude_config_example.json` file in the installation directory. Copy its contents to:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Example configuration:
```json
{
  "mcpServers": {
    "matlab": {
      "command": "C:\\Program Files\\MATLAB MCP Server\\matlab-mcp-server.exe",
      "env": {
        "MATLAB_PATH": "C:\\Program Files\\MATLAB\\R2024b"
      }
    }
  }
}
```

#### If using built executable:
```json
{
  "mcpServers": {
    "matlab": {
      "command": "/absolute/path/to/dist/matlab-mcp-server/matlab-mcp-server.exe",
      "env": {
        "MATLAB_PATH": "C:\\Program Files\\MATLAB\\R2024b"
      }
    }
  }
}
```

#### If using development installation:
```json
{
  "mcpServers": {
    "matlab": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/matlab-mcp-server/src/matlab_mcp_server/server.py"],
      "env": {
        "MATLAB_PATH": "/Applications/MATLAB_R2024b.app"
      }
    }
  }
}
```

**Config file locations:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## Available Tools

### Code Execution
- `execute_matlab_code` - Execute MATLAB code with full output capture
- `get_workspace_variable` - Retrieve variables from MATLAB workspace
- `list_workspace` - List all variables in workspace
- `clear_workspace` - Clear MATLAB workspace

### Output & Export
- `export_figure` - Export current figure to PNG/SVG/PDF/LaTeX
- `export_all_figures` - Export all open figures
- `get_symbolic_latex` - Convert symbolic expressions to LaTeX
- `save_matlab_script` - Save code to .m file

### Project Management
- `set_project` - Set current project (creates directory in Documents/MATLAB_Projects)
- `get_current_project` - Show current project and output directory
- `list_projects` - List all available projects

## Usage Examples

### Working with Projects
```
Set project to "MyAnalysis"
```

All output files (figures, scripts) will automatically save to:
`C:\Users\<YourName>\Documents\MATLAB_Projects\MyAnalysis\`

The project persists for the entire session, so all subsequent exports go to the same location.

### Execute MATLAB Code
```
Execute this MATLAB code:
x = 0:0.1:10;
y = sin(x);
plot(x, y);
title('Sine Wave');
```

### Export Figures
```
Export the current figure as a high-resolution PNG
```

The figure will be saved to the current project directory if one is set, otherwise to the default workspace directory.

### Work with Symbolic Math
```
Create a symbolic equation and export it to LaTeX
```

### Complete Workflow Example
```
1. Set project to "SignalAnalysis"
2. Execute MATLAB code to generate a plot
3. Export the figure as PNG and SVG
4. Save the code as a script file
```

All files will be organized in `Documents/MATLAB_Projects/SignalAnalysis/`

## Troubleshooting

### MATLAB Engine Installation Issues
- Ensure Python 3.11 is being used (check with `python --version`)
- Verify MATLAB path is correct in .env file
- Run MATLAB Engine setup with admin/sudo if permission errors occur

### Output Not Captured
- Check that StringIO redirection is working
- Verify MATLAB Engine session is active
- Look for errors in MCP server logs

## License

MIT License - see LICENSE file for details
