#!/usr/bin/env python3
"""Test MATLAB execution directly without MCP."""

import sys
import os
os.environ["MATLAB_PATH"] = r"C:\Program Files\MATLAB\R2025b"

# Add src to path
sys.path.insert(0, r'C:\projects\matlabserver\src')

from matlab_mcp_server.matlab_engine_wrapper import MATLABEngineWrapper

def test_direct():
    print("Creating wrapper...")
    wrapper = MATLABEngineWrapper(os.environ["MATLAB_PATH"])

    print("Starting MATLAB...")
    result = wrapper.start()
    if not result["success"]:
        print(f"Failed to start: {result}")
        return

    print("MATLAB started successfully!")

    print("Executing code...")
    result = wrapper.execute("disp('Hello from direct test')", capture_output=True)

    print(f"Result: {result}")

    print("Stopping engine...")
    wrapper.stop()
    print("Done!")

if __name__ == "__main__":
    test_direct()