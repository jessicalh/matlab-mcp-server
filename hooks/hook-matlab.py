"""PyInstaller hook for MATLAB Engine API."""

from PyInstaller.utils.hooks import collect_all

# Collect all matlab package data, binaries, and hidden imports
datas, binaries, hiddenimports = collect_all('matlab')

# Add specific hidden imports that might not be auto-detected
hiddenimports += [
    'matlab.engine',
    'matlab.mlarray',
    'matlab.mlexceptions',
]
