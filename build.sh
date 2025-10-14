#!/bin/bash
# Build script for MATLAB MCP Server (macOS/Linux)
# This script builds the PyInstaller executable

set -e

echo "========================================"
echo "MATLAB MCP Server Build Script"
echo "========================================"
echo ""

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11 is required but not found."
    echo "Please install Python 3.11 and try again."
    exit 1
fi

echo "Found Python: $(python3.11 --version)"
echo ""

# Check if MATLAB_PATH is set
if [ -z "$MATLAB_PATH" ]; then
    echo "Warning: MATLAB_PATH environment variable is not set."
    echo "The build may fail if MATLAB Engine API cannot be found."
    echo ""
    read -p "Enter MATLAB installation path (e.g., /Applications/MATLAB_R2024b.app): " MATLAB_PATH
    export MATLAB_PATH
fi

echo "Using MATLAB_PATH: $MATLAB_PATH"
echo ""

# Step 1: Install dependencies
echo "========================================"
echo "Step 1: Installing dependencies"
echo "========================================"
echo ""

python3.11 -m pip install --upgrade pip
pip install -e .[build]

echo "Dependencies installed successfully"
echo ""

# Step 2: Install MATLAB Engine API
echo "========================================"
echo "Step 2: Checking MATLAB Engine API"
echo "========================================"
echo ""

if ! python3.11 -c "import matlab.engine" 2>/dev/null; then
    echo "MATLAB Engine API not found. Attempting to install..."
    echo ""

    MATLAB_ENGINE_PATH="$MATLAB_PATH/extern/engines/python"
    if [ -f "$MATLAB_ENGINE_PATH/setup.py" ]; then
        echo "Found MATLAB Engine API at: $MATLAB_ENGINE_PATH"
        cd "$MATLAB_ENGINE_PATH"
        python3.11 setup.py install
        cd -
        echo "MATLAB Engine API installed successfully"
    else
        echo "Error: Could not find MATLAB Engine API at expected location"
        echo "Please install it manually from: $MATLAB_PATH/extern/engines/python"
        exit 1
    fi
else
    echo "MATLAB Engine API is already installed"
fi
echo ""

# Step 3: Build with PyInstaller
echo "========================================"
echo "Step 3: Building executable with PyInstaller"
echo "========================================"
echo ""

# Clean previous builds
rm -rf dist/matlab-mcp-server build

# Run PyInstaller
pyinstaller matlab-mcp-server.spec

echo "PyInstaller build completed successfully"
echo ""

echo "========================================"
echo "Build Complete!"
echo "========================================"
echo ""
echo "Outputs:"
echo "- Executable: dist/matlab-mcp-server/matlab-mcp-server"
echo ""
echo "To test the executable:"
echo "  dist/matlab-mcp-server/matlab-mcp-server"
echo ""
