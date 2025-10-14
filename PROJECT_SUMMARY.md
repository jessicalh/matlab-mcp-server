# MATLAB MCP Server - Project Summary

## Overview

A complete Model Context Protocol (MCP) server implementation for local MATLAB integration with Claude Desktop. This project enables AI assistants to execute MATLAB code, capture debugging output, export figures in multiple formats, and manage workspace variables—all without requiring a MATLAB Web Server license.

## Key Features

### 1. Comprehensive Output Capture
- Captures all stdout and stderr from MATLAB execution
- Redirects output using Python StringIO for complete debugging visibility
- Returns warnings, errors, and all console messages to the MCP client

### 2. Multi-Format Export
- **Figures**: PNG, SVG, PDF, EPS, JPEG, TIFF
- **LaTeX**: Convert symbolic expressions to LaTeX format
- **Scripts**: Save MATLAB code to .m files
- Configurable DPI for raster formats
- Uses modern `exportgraphics` API with fallback to `print`

### 3. Workspace Management
- List all variables with types and sizes
- Retrieve variable values and metadata
- Clear specific variables or entire workspace
- Persistent MATLAB session for fast execution

### 4. Windows Installer
- Professional Inno Setup installer
- Automatic MATLAB path detection
- Creates configuration files automatically
- Guides user through Claude Desktop setup

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
└────────┬────────┘
         │ stdio (JSON-RPC)
         ↓
┌─────────────────┐
│  MCP Server     │  (Python with MCP SDK)
│  (server.py)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ MATLAB Engine   │  (Python API wrapper)
│ Wrapper         │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Local MATLAB    │  (R2020b+)
└─────────────────┘
```

## Project Structure

```
matlab-mcp-server/
├── src/
│   └── matlab_mcp_server/
│       ├── __init__.py              # Package initialization
│       ├── server.py                # MCP server implementation
│       └── matlab_engine_wrapper.py # MATLAB Engine API wrapper
├── hooks/
│   ├── hook-matlab.py               # PyInstaller hook for MATLAB
│   └── hook-mcp.py                  # PyInstaller hook for MCP
├── installer/
│   ├── setup.iss                    # Inno Setup installer script
│   └── INSTALL_INFO.txt             # Pre-installation information
├── matlab-mcp-server.spec           # PyInstaller spec file
├── build.bat                        # Windows build script
├── build.sh                         # Unix build script
├── pyproject.toml                   # Python project configuration
├── .env.example                     # Environment variable template
├── README.md                        # User documentation
├── BUILD.md                         # Build instructions
└── LICENSE                          # MIT License
```

## Available MCP Tools

### Code Execution & Workspace
1. **execute_matlab_code**
   - Execute arbitrary MATLAB code
   - Full stdout/stderr capture
   - Error handling and debugging info

2. **get_workspace_variable**
   - Retrieve specific workspace variable
   - Includes value, type, and size metadata

3. **list_workspace**
   - List all workspace variables
   - Shows types and dimensions

4. **clear_workspace**
   - Clear specific variables or all

### Output & Export
5. **export_figure**
   - Export current or specific figure
   - Multiple format support (PNG, SVG, PDF, EPS, JPEG, TIFF)
   - Configurable resolution

6. **export_all_figures**
   - Batch export all open figures
   - Same format options as single export

7. **get_symbolic_latex**
   - Convert symbolic expressions to LaTeX
   - Uses MATLAB Symbolic Math Toolbox

8. **save_matlab_script**
   - Save code to .m files
   - Organized in workspace directory

### Project Management (NEW)
9. **set_project**
   - Set current project for session
   - Creates directory in Documents/MATLAB_Projects/<project_name>
   - All output files automatically saved to project directory
   - Persists for entire session

10. **get_current_project**
    - Show current active project
    - Display project directory path
    - Show workspace directory location

11. **list_projects**
    - List all projects in MATLAB_Projects directory
    - Shows which project is currently active
    - Helps users switch between different workspaces

## Technical Implementation Details

### MATLAB Engine API Integration
- Uses official MATLAB Engine API for Python
- Supports Python 3.11-3.13 (tested with 3.13)
- Persistent session maintains workspace state
- Non-blocking execution possible with async support
- Project-based output directory management

### Output Capture Strategy
```python
stdout_buffer = io.StringIO()
stderr_buffer = io.StringIO()
engine.eval(code, nargout=0, stdout=stdout_buffer, stderr=stderr_buffer)
```

### PyInstaller Bundling
- Custom hooks collect MATLAB module dependencies
- Adds MATLAB bin path to executable search paths
- Bundles all MCP SDK requirements
- Creates standalone executable with all dependencies

### Windows Installer Features
- Interactive MATLAB path selection with validation
- Automatic .env file generation
- Creates claude_config_example.json with correct paths
- Post-install instructions displayed in MessageBox
- Proper uninstall support

## Build System

### Automated Build Process
1. **Dependency Installation**
   - Python packages via pip
   - MATLAB Engine API from MATLAB installation

2. **PyInstaller Compilation**
   - Processes spec file with custom hooks
   - Bundles Python interpreter and dependencies
   - Creates distributable executable directory

3. **Installer Creation** (Windows)
   - Compiles Inno Setup script
   - Packages executable with documentation
   - Creates single-file installer

### Build Requirements
- Python 3.11
- MATLAB R2020b+ with Engine API
- PyInstaller 6.0+
- Inno Setup 6.0+ (Windows installer only)

## Distribution Options

### 1. Windows Installer (.exe)
- **Target Users**: End users on Windows
- **Size**: ~50-100 MB (depends on dependencies)
- **Requirements**: MATLAB installed locally
- **Advantages**:
  - One-click installation
  - Guided setup process
  - Automatic configuration
  - Professional user experience

### 2. Standalone Executable
- **Target Users**: All platforms (Windows/macOS/Linux)
- **Size**: ~40-80 MB per platform
- **Requirements**: MATLAB with Engine API installed
- **Advantages**:
  - No Python installation needed
  - Portable (copy to any machine)
  - Fast execution

### 3. Source Installation
- **Target Users**: Developers
- **Requirements**: Python 3.11, MATLAB, pip
- **Advantages**:
  - Full access to source code
  - Easy to modify and extend
  - Development workflow

## Configuration

### Environment Variables
- `MATLAB_PATH`: Path to MATLAB installation (required)
- `MATLAB_WORKSPACE_DIR`: Directory for scripts/exports (optional)
- `MATLAB_FIGURE_DPI`: Default export resolution (optional)

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "matlab": {
      "command": "<path-to-executable>",
      "env": {
        "MATLAB_PATH": "<matlab-installation-path>"
      }
    }
  }
}
```

## Development Workflow

### Setting Up Development Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e .[dev]
cd $MATLAB_PATH/extern/engines/python
python setup.py install
```

### Running in Development Mode
```bash
python src/matlab_mcp_server/server.py
```

### Building for Distribution
```bash
# Windows
build.bat

# macOS/Linux
./build.sh
```

### Testing
```bash
# Unit tests (if implemented)
pytest

# Manual testing with MCP Inspector
mcp-inspector dist/matlab-mcp-server/matlab-mcp-server
```

## Troubleshooting Common Issues

### MATLAB Engine API Installation
- Ensure Python 3.11 is being used
- Check MATLAB_PATH is correct
- May need admin/sudo permissions

### PyInstaller Build Failures
- Verify all hooks are in place
- Check MATLAB bin path in spec file
- Ensure MATLAB Engine is importable

### Runtime Issues
- MATLAB must be installed on target machine
- MATLAB_PATH must point to valid installation
- Check Claude Desktop config syntax

## Future Enhancements

### Potential Features
- [ ] Simulink integration
- [ ] Real-time plotting/streaming
- [ ] Parallel computation support
- [ ] MATLAB package/toolbox detection
- [ ] Code completion suggestions
- [ ] Enhanced error messages with MATLAB docs links
- [ ] Performance profiling tools
- [ ] Breakpoint debugging support

### Platform Support
- [ ] Linux installer (deb/rpm packages)
- [ ] macOS installer (.pkg)
- [ ] Docker container option
- [ ] Cloud deployment guide

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing documentation (README.md, BUILD.md)
- Review troubleshooting sections

## Acknowledgments

- Anthropic for the Model Context Protocol specification
- MathWorks for the MATLAB Engine API for Python
- PyInstaller and Inno Setup teams for excellent tools
