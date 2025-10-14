# Building MATLAB MCP Server

This guide explains how to build the MATLAB MCP Server executable and Windows installer from source.

## Prerequisites

### Required Software

1. **Python 3.11**
   - Download from [python.org](https://www.python.org/downloads/)
   - **Important**: Python 3.11 is required for MATLAB Engine API compatibility
   - Ensure Python is added to your PATH

2. **MATLAB Installation**
   - R2020b or later recommended
   - Note the installation path (needed for building)

3. **Git** (for cloning the repository)
   - Windows: [Git for Windows](https://git-scm.com/download/win)
   - macOS: Included with Xcode Command Line Tools
   - Linux: Install via package manager

4. **Inno Setup** (Windows only, for creating installer)
   - Download from [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)
   - Version 6.0 or later required
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

### Environment Setup

Set the `MATLAB_PATH` environment variable to your MATLAB installation:

**Windows:**
```batch
set MATLAB_PATH=C:\Program Files\MATLAB\R2024b
```

**macOS:**
```bash
export MATLAB_PATH=/Applications/MATLAB_R2024b.app
```

**Linux:**
```bash
export MATLAB_PATH=/usr/local/MATLAB/R2024b
```

## Build Process

### Windows

1. **Open Command Prompt** and navigate to the project directory:
   ```batch
   cd C:\path\to\matlab-mcp-server
   ```

2. **Set MATLAB path** (if not already in environment):
   ```batch
   set MATLAB_PATH=C:\Program Files\MATLAB\R2024b
   ```

3. **Run the build script**:
   ```batch
   build.bat
   ```

The script will:
- Check for Python 3.11
- Install Python dependencies (including PyInstaller)
- Install MATLAB Engine API for Python
- Build the executable with PyInstaller
- Create the Windows installer with Inno Setup

**Build outputs:**
- Executable: `dist\matlab-mcp-server\matlab-mcp-server.exe`
- Installer: `dist\installer\matlab-mcp-server-setup-0.1.0.exe`

### macOS/Linux

1. **Open Terminal** and navigate to the project directory:
   ```bash
   cd /path/to/matlab-mcp-server
   ```

2. **Set MATLAB path** (if not already in environment):
   ```bash
   export MATLAB_PATH=/Applications/MATLAB_R2024b.app  # macOS
   # or
   export MATLAB_PATH=/usr/local/MATLAB/R2024b  # Linux
   ```

3. **Run the build script**:
   ```bash
   ./build.sh
   ```

The script will:
- Check for Python 3.11
- Install Python dependencies
- Install MATLAB Engine API for Python
- Build the executable with PyInstaller

**Build output:**
- Executable: `dist/matlab-mcp-server/matlab-mcp-server`

## Manual Build Steps

If you prefer to build manually or troubleshoot issues:

### 1. Install Dependencies

```bash
# Create virtual environment (optional but recommended)
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python packages
pip install -e .[build]
```

### 2. Install MATLAB Engine API

**Windows:**
```batch
cd "%MATLAB_PATH%\extern\engines\python"
python setup.py install
cd /d %~dp0
```

**macOS/Linux:**
```bash
cd "$MATLAB_PATH/extern/engines/python"
python setup.py install
cd -
```

### 3. Build with PyInstaller

```bash
# Clean previous builds
rm -rf dist/matlab-mcp-server build  # Unix
# or
rmdir /s /q dist\matlab-mcp-server build  # Windows

# Build executable
pyinstaller matlab-mcp-server.spec
```

### 4. Create Windows Installer (Windows only)

If you have Inno Setup installed:

```batch
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
```

Or open `installer\setup.iss` in Inno Setup and click "Build > Compile".

## Troubleshooting

### Python Version Issues

**Error**: "Python 3.11 is required but not found"

**Solution**: Ensure Python 3.11 is installed and accessible:
```bash
python3.11 --version  # Should show 3.11.x
```

### MATLAB Engine API Installation Fails

**Error**: Cannot find MATLAB Engine API setup.py

**Solution**:
1. Verify MATLAB_PATH is correct
2. Check that the path exists:
   ```bash
   # Windows
   dir "%MATLAB_PATH%\extern\engines\python\setup.py"

   # Unix
   ls "$MATLAB_PATH/extern/engines/python/setup.py"
   ```

### PyInstaller Import Errors

**Error**: "ModuleNotFoundError: No module named 'matlab'"

**Solution**: Ensure MATLAB Engine API is installed in your Python environment:
```bash
python -c "import matlab.engine; print('OK')"
```

### Inno Setup Not Found

**Error**: "Inno Setup not found at default location"

**Solution**:
- Install Inno Setup from [jrsoftware.org](https://jrsoftware.org/isinfo.php)
- Or manually compile `installer\setup.iss` using Inno Setup GUI

### Permission Errors

**Error**: Permission denied when installing MATLAB Engine API

**Solution** (Windows): Run Command Prompt as Administrator

**Solution** (macOS/Linux): Use sudo if necessary:
```bash
sudo python setup.py install
```

## Testing the Build

### Test the Executable

**Windows:**
```batch
dist\matlab-mcp-server\matlab-mcp-server.exe
```

**macOS/Linux:**
```bash
dist/matlab-mcp-server/matlab-mcp-server
```

The server should start and wait for stdio input. Press Ctrl+C to exit.

### Test with MCP Inspector

Install the MCP Inspector for debugging:

```bash
npm install -g @modelcontextprotocol/inspector
```

Run the inspector:
```bash
# Windows
mcp-inspector dist\matlab-mcp-server\matlab-mcp-server.exe

# macOS/Linux
mcp-inspector dist/matlab-mcp-server/matlab-mcp-server
```

## Build Customization

### Modify PyInstaller Build

Edit `matlab-mcp-server.spec` to customize:
- Hidden imports
- Data files to include
- Binary paths
- Executable name and options

### Modify Installer

Edit `installer/setup.iss` to customize:
- App name and version
- Installation directory
- Shortcuts and icons
- Pre/post-install actions

## Distribution

### Distributing the Executable

The `dist/matlab-mcp-server/` directory contains a standalone executable with all dependencies. You can:
- Zip the entire directory and distribute
- Copy to any Windows/macOS/Linux machine with MATLAB installed
- No Python installation required on target machine

**Note**: The target machine still needs:
- MATLAB installed locally
- MATLAB Engine API for Python installed (can be bundled or installed separately)

### Distributing the Windows Installer

The `dist/installer/matlab-mcp-server-setup-X.X.X.exe` is a complete installer that:
- Copies all files to Program Files
- Guides user to select MATLAB installation
- Creates configuration files
- Provides setup instructions

Users only need:
- Windows OS
- MATLAB installed

## Continuous Integration

For automated builds, see `.github/workflows/build.yml` (if available) or create your own CI pipeline:

```yaml
# Example GitHub Actions workflow
name: Build
on: [push, pull_request]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Build
        run: build.bat
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: installer
          path: dist/installer/
```

## Support

For build issues, please:
1. Check this guide's troubleshooting section
2. Review build script output for errors
3. Open an issue on GitHub with build logs
