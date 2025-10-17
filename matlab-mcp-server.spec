# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for MATLAB MCP Server."""

import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Determine MATLAB installation path from environment
matlab_path = os.getenv('MATLAB_PATH', '')
matlab_bin_path = ''

if matlab_path:
    if sys.platform == 'win32':
        # Windows: C:\Program Files\MATLAB\R2024b\extern\bin\win64
        matlab_bin_path = os.path.join(matlab_path, 'extern', 'bin', 'win64')
    elif sys.platform == 'darwin':
        # macOS: /Applications/MATLAB_R2024b.app/bin/maci64
        matlab_bin_path = os.path.join(matlab_path, 'bin', 'maci64')
    else:
        # Linux: /usr/local/MATLAB/R2024b/bin/glnxa64
        matlab_bin_path = os.path.join(matlab_path, 'bin', 'glnxa64')

# Collect all data and imports for dependencies
matlab_datas, matlab_binaries, matlab_hiddenimports = collect_all('matlab')
mcp_datas, mcp_binaries, mcp_hiddenimports = collect_all('mcp')

# Combine all collections
datas = matlab_datas + mcp_datas + [
    ('.env.example', '.'),
]
binaries = matlab_binaries + mcp_binaries
hiddenimports = matlab_hiddenimports + mcp_hiddenimports + [
    'matlab.engine',
    'matlab.mlarray',
    'matlab.mlexceptions',
    'mcp.server',
    'mcp.server.stdio',
    'mcp.types',
    'dotenv',
]

# Analysis
a = Analysis(
    ['src/matlab_mcp_server/main.py'],
    pathex=[
        'src/matlab_mcp_server',
        matlab_bin_path,  # Add MATLAB bin path
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Process files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='matlab-mcp-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Must be console app for stdio communication
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect everything into a directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='matlab-mcp-server',
)
