#!/usr/bin/env python3
"""Automated MCP Inspector test script for MATLAB MCP Server."""

import subprocess
import json
import sys
import os

# Path to executable
EXECUTABLE_PATH = r"C:\projects\matlabserver\dist\matlab-mcp-server\matlab-mcp-server.exe"
MATLAB_PATH = r"C:\Program Files\MATLAB\R2025b"

def run_mcp_command(method, **kwargs):
    """Run an MCP Inspector command and return JSON result."""
    cmd = [
        "npx",
        "@modelcontextprotocol/inspector",
        "--cli",
        EXECUTABLE_PATH
    ]

    # Set environment
    env = os.environ.copy()
    env["MATLAB_PATH"] = MATLAB_PATH

    # Add method
    cmd.extend(["--method", method])

    # Add additional arguments
    for key, value in kwargs.items():
        cmd.extend([f"--{key}", str(value)])

    print(f"\n[TEST] Running: {method}")
    print(f"       Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )

        print(f"       Status: {'SUCCESS' if result.returncode == 0 else 'FAILED'}")

        if result.stdout:
            try:
                data = json.loads(result.stdout)
                print(f"       Output: {json.dumps(data, indent=2)[:200]}...")
                return data
            except json.JSONDecodeError:
                print(f"       Output (non-JSON): {result.stdout[:200]}")
                return result.stdout

        if result.stderr:
            print(f"       Error: {result.stderr[:200]}")

        return None

    except subprocess.TimeoutExpired:
        print("       Status: TIMEOUT")
        return None
    except Exception as e:
        print(f"       Exception: {e}")
        return None


def main():
    """Run automated tests."""
    print("=" * 60)
    print("MATLAB MCP Server - Automated Testing")
    print("=" * 60)

    print(f"\nExecutable: {EXECUTABLE_PATH}")
    print(f"MATLAB Path: {MATLAB_PATH}")

    # Test 1: List available tools
    print("\n" + "=" * 60)
    print("TEST 1: List Tools")
    print("=" * 60)
    result = run_mcp_command("tools/list")

    # Test 2: Execute simple MATLAB code
    print("\n" + "=" * 60)
    print("TEST 2: Execute Simple Code")
    print("=" * 60)
    test_code = "x = 1 + 1; disp(x)"
    result = run_mcp_command(
        "tools/call",
        tool_name="execute_matlab_code",
        tool_arg=f"code={test_code}"
    )

    # Test 3: List workspace
    print("\n" + "=" * 60)
    print("TEST 3: List Workspace")
    print("=" * 60)
    result = run_mcp_command(
        "tools/call",
        tool_name="list_workspace"
    )

    # Test 4: Create a figure (validation test)
    print("\n" + "=" * 60)
    print("TEST 4: Create Figure")
    print("=" * 60)
    test_code = "x=0:0.1:2*pi; plot(x,sin(x)); title('Test Plot');"
    result = run_mcp_command(
        "tools/call",
        tool_name="execute_matlab_code",
        tool_arg=f"code={test_code}"
    )

    # Test 5: Test blank figure detection
    print("\n" + "=" * 60)
    print("TEST 5: Blank Figure Detection")
    print("=" * 60)
    test_code = "figure();"  # Creates blank figure
    result = run_mcp_command(
        "tools/call",
        tool_name="execute_matlab_code",
        tool_arg=f"code={test_code}"
    )

    # Test 6: Test critical warning detection (singular matrix)
    print("\n" + "=" * 60)
    print("TEST 6: Critical Warning Detection")
    print("=" * 60)
    test_code = "A = [1 2; 2 4]; b = [1; 2]; x = A\\b;"  # Singular matrix
    result = run_mcp_command(
        "tools/call",
        tool_name="execute_matlab_code",
        tool_arg=f"code={test_code}"
    )

    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)
    print("\nCheck matlab_mcp_server.log for detailed logs")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
