@echo off
cd /d "C:\projects\matlabserver"
set PYTHONWARNINGS=ignore
"C:\Program Files\Python313\python.exe" -W ignore -m src.matlab_mcp_server.server