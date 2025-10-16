@echo off
REM Build script for MATLAB MCP Server Windows installer
REM This script builds the PyInstaller executable and creates the Inno Setup installer

echo ========================================
echo MATLAB MCP Server Build Script
echo ========================================
echo.

REM Check if Python 3.11+ is available
python --version 2>NUL | findstr /C:"Python 3.1" >NUL
if errorlevel 1 (
    echo Error: Python 3.11 or later is required but not found.
    echo Please install Python 3.11+ and ensure it's in your PATH.
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%
echo.

REM Check if MATLAB_PATH is set
if not defined MATLAB_PATH (
    echo Warning: MATLAB_PATH environment variable is not set.
    echo The build may fail if MATLAB Engine API cannot be found.
    echo.
    set /p MATLAB_PATH="Enter MATLAB installation path (e.g., C:\Program Files\MATLAB\R2024b): "
)

echo Using MATLAB_PATH: %MATLAB_PATH%
echo.

REM Step 1: Install dependencies
echo ========================================
echo Step 1: Installing dependencies
echo ========================================
echo.

python -m pip install --upgrade pip
if errorlevel 1 (
    echo Error: Failed to upgrade pip
    exit /b 1
)

pip install -e .[build]
if errorlevel 1 (
    echo Error: Failed to install dependencies
    exit /b 1
)

echo Dependencies installed successfully
echo.

REM Step 2: Install MATLAB Engine API
echo ========================================
echo Step 2: Checking MATLAB Engine API
echo ========================================
echo.

python -c "import matlab.engine" 2>NUL
if errorlevel 1 (
    echo MATLAB Engine API not found. Attempting to install...
    echo.

    set MATLAB_ENGINE_PATH=%MATLAB_PATH%\extern\engines\python
    if exist "%MATLAB_ENGINE_PATH%\setup.py" (
        echo Found MATLAB Engine API at: %MATLAB_ENGINE_PATH%
        pushd "%MATLAB_ENGINE_PATH%"
        python setup.py install
        popd

        if errorlevel 1 (
            echo Error: Failed to install MATLAB Engine API
            exit /b 1
        )
        echo MATLAB Engine API installed successfully
    ) else (
        echo Error: Could not find MATLAB Engine API at expected location
        echo Please install it manually from: %MATLAB_PATH%\extern\engines\python
        exit /b 1
    )
) else (
    echo MATLAB Engine API is already installed
)
echo.

REM Step 3: Build with PyInstaller
echo ========================================
echo Step 3: Building executable with PyInstaller
echo ========================================
echo.

REM Clean previous builds
if exist dist\matlab-mcp-server rmdir /s /q dist\matlab-mcp-server
if exist build rmdir /s /q build

REM Run PyInstaller
pyinstaller matlab-mcp-server.spec
if errorlevel 1 (
    echo Error: PyInstaller build failed
    exit /b 1
)

echo PyInstaller build completed successfully
echo.

REM Step 4: Create installer with Inno Setup
echo ========================================
echo Step 4: Creating Windows installer
echo ========================================
echo.

REM Check if Inno Setup is installed
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% (
    echo Warning: Inno Setup not found at default location
    echo Please install Inno Setup 6 from https://jrsoftware.org/isinfo.php
    echo.
    echo You can manually create the installer by:
    echo 1. Install Inno Setup
    echo 2. Open installer\setup.iss
    echo 3. Click Build -^> Compile
    echo.
    goto :skip_installer
)

REM Create LICENSE file if it doesn't exist
if not exist LICENSE (
    echo MIT License > LICENSE
    echo. >> LICENSE
    echo Copyright ^(c^) 2025 MATLAB MCP Server Project >> LICENSE
)

REM Build installer
%INNO_SETUP% installer\setup.iss
if errorlevel 1 (
    echo Error: Inno Setup build failed
    exit /b 1
)

echo Installer created successfully
echo.

:skip_installer

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Outputs:
echo - Executable: dist\matlab-mcp-server\matlab-mcp-server.exe
if exist dist\installer\matlab-mcp-server-setup-0.1.0.exe (
    echo - Installer:  dist\installer\matlab-mcp-server-setup-0.1.0.exe
)
echo.
echo To test the executable directly:
echo   dist\matlab-mcp-server\matlab-mcp-server.exe
echo.

pause
