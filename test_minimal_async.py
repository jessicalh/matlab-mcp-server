#!/usr/bin/env python3
"""Minimal test to see if async MATLAB initialization works."""

import asyncio
import sys
import os

# Set up environment
os.environ["MATLAB_PATH"] = r"C:\Program Files\MATLAB\R2025b"

async def test_async_matlab():
    """Test async MATLAB initialization."""

    print("Starting test...")

    # Import the server module
    from matlab_mcp_server.matlab_engine_wrapper import MATLABEngineWrapper

    # Create wrapper
    print("Creating wrapper...")
    wrapper = MATLABEngineWrapper(os.environ["MATLAB_PATH"])

    # Start engine asynchronously
    print("Starting MATLAB engine asynchronously...")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, wrapper.start)

    if result["success"]:
        print(f"SUCCESS: MATLAB started! Version: {result.get('matlab_version')}")

        # Test execution
        print("Testing execution...")
        exec_result = await loop.run_in_executor(
            None,
            wrapper.execute,
            "disp('Hello from async test')",
            True  # capture_output
        )

        if exec_result["success"]:
            print(f"Execution SUCCESS: {exec_result.get('stdout', '').strip()}")
        else:
            print(f"Execution FAILED: {exec_result.get('error')}")

        # Stop engine
        print("Stopping engine...")
        wrapper.stop()
    else:
        print(f"FAILED: {result.get('error')}")

    print("Test complete!")

if __name__ == "__main__":
    print(f"Python: {sys.version}")
    asyncio.run(test_async_matlab())