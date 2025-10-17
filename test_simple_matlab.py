#!/usr/bin/env python3
"""Simple test to see if MATLAB Engine itself is working."""

import sys
import os
import matlab.engine
import io

print("Starting test...")

# Start MATLAB engine
print("Starting MATLAB engine...")
engine = matlab.engine.start_matlab()
print("MATLAB engine started!")

# Test 1: Simple eval without output capture
print("\nTest 1: Simple eval without capture...")
try:
    engine.eval("disp('Hello from MATLAB')", nargout=0)
    print("SUCCESS: Simple eval worked!")
except Exception as e:
    print(f"FAILED: {e}")

# Test 2: Eval with stdout capture
print("\nTest 2: Eval with stdout capture...")
try:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    engine.eval("disp('Hello with capture')", nargout=0, stdout=stdout_buf, stderr=stderr_buf)
    output = stdout_buf.getvalue()
    print(f"SUCCESS: Got output: {repr(output)}")
except Exception as e:
    print(f"FAILED: {e}")

# Test 3: Run in a thread (simulating asyncio.run_in_executor)
print("\nTest 3: Run in thread...")
import concurrent.futures
try:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(
            lambda: engine.eval("disp('Hello from thread')", nargout=0)
        )
        result = future.result(timeout=5)
        print("SUCCESS: Thread execution worked!")
except Exception as e:
    print(f"FAILED: {e}")

# Test 4: Run with capture in thread
print("\nTest 4: Run with capture in thread...")
try:
    def execute_with_capture():
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        engine.eval("disp('Thread with capture')", nargout=0, stdout=stdout_buf, stderr=stderr_buf)
        return stdout_buf.getvalue()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(execute_with_capture)
        output = future.result(timeout=5)
        print(f"SUCCESS: Got output from thread: {repr(output)}")
except Exception as e:
    print(f"FAILED: {e}")

print("\nCleaning up...")
engine.quit()
print("Done!")