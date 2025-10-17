# MATLAB MCP Server Setup Instructions

## For Another Claude Instance

### Prerequisites
1. **MATLAB R2025b** installed at `C:\Program Files\MATLAB\R2025b`
2. **Python 3.9-3.12** (3.13 works with warnings)
3. **Git** installed
4. **PyInstaller** (`pip install pyinstaller`)
5. **MCP SDK** (`pip install mcp`)

### Repository Setup
```bash
git clone https://github.com/[username]/matlab-mcp-server.git
cd matlab-mcp-server
```

### Environment Setup
1. Create `.env` file:
```
MATLAB_PATH=C:\Program Files\MATLAB\R2025b
MATLAB_WORKSPACE_DIR=./matlab_workspace
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install MATLAB Engine for Python:
```bash
cd "C:\Program Files\MATLAB\R2025b\extern\engines\python"
python setup.py install
```

### Build Process
```bash
# Build the executable
pyinstaller matlab-mcp-server.spec --noconfirm

# Test the build
python test_mcp_init.py --exe
```

### Claude Desktop Configuration
Add to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "matlab": {
      "command": "C:\\projects\\matlabserver\\dist\\matlab-mcp-server\\matlab-mcp-server.exe",
      "env": {
        "MATLAB_PATH": "C:\\Program Files\\MATLAB\\R2025b",
        "MATLAB_WORKSPACE_DIR": "C:\\projects\\matlabserver\\matlab_workspace"
      }
    }
  }
}
```

### Critical Implementation Notes

#### Thread Affinity Fix (IMPORTANT)
The MATLAB Engine API has thread affinity issues. The fix applied:
1. Removed pre-execution MATLAB calls in `execute()` method
2. Used thread-local storage for engine instances
3. Used `asyncio.to_thread()` for async/sync coordination
4. Simplified validation to avoid blocking calls

Key changes in `src/matlab_mcp_server/matlab_engine_wrapper.py`:
- Skipped `_get_figure_handles()` before execution
- Skipped warning clearing before execution
- Simplified validation checks

Key changes in `src/matlab_mcp_server/server.py`:
- Thread-local storage for MATLAB engine
- `asyncio.to_thread()` for execute calls

#### Testing
Run `python test_mcp_init.py` to verify:
1. MCP protocol initialization
2. MATLAB code execution
3. Figure creation and export

### Known Issues
- MATLAB Engine Python 3.13 compatibility warnings (works but shows warnings)
- Figure detection disabled to avoid thread blocking
- Validation simplified to avoid thread issues

### Development Notes
- Main branch: main
- Test with `python test_mcp_init.py` for Python version
- Test with `python test_mcp_init.py --exe` for PyInstaller version
- Logs in `matlab_mcp_server.log` and `call_tool_debug.log`

### Version Info
- Current version: 0.2.1 Alpha (fixed)
- MATLAB tested: R2025b only
- Python tested: 3.13 (with warnings)
- Windows only

### Contact
For issues, check the error logs first. The main blocking issue was thread affinity with MATLAB Engine API - this has been fixed by simplifying pre-execution checks.