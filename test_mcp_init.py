#!/usr/bin/env python3
"""Test MCP initialization sequence - simulates what Claude Desktop does."""

import json
import asyncio
import sys
from typing import Any, Dict

# JSON-RPC 2.0 message ID counter
message_id = 0

def create_jsonrpc_request(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a JSON-RPC 2.0 request."""
    global message_id
    message_id += 1
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "id": message_id
    }
    if params is not None:
        request["params"] = params
    return request

async def send_message(writer, message: Dict[str, Any]):
    """Send a JSON-RPC message over stdio."""
    json_str = json.dumps(message)
    print(f">>> Sending: {json_str}", file=sys.stderr)
    writer.write(json_str.encode() + b'\n')
    await writer.drain()

async def receive_message(reader) -> Dict[str, Any]:
    """Receive a JSON-RPC message over stdio."""
    line = await reader.readline()
    if not line:
        print("<<< EOF received", file=sys.stderr)
        return None
    json_str = line.decode().strip()
    print(f"<<< Received: {json_str}", file=sys.stderr)
    return json.loads(json_str) if json_str else None

async def test_mcp_server():
    """Test the MCP server with proper initialization sequence."""

    # Start the server as a subprocess
    if len(sys.argv) > 1 and sys.argv[1] == '--exe':
        # Test the PyInstaller executable
        cmd = r'C:\projects\matlabserver\dist\matlab-mcp-server\matlab-mcp-server.exe'
        print(f"Testing PyInstaller executable: {cmd}", file=sys.stderr)
    else:
        # Test Python directly
        cmd = sys.executable
        args = ['-m', 'matlab_mcp_server.server']
        print(f"Testing Python module: {cmd} {' '.join(args)}", file=sys.stderr)

    if len(sys.argv) > 1 and sys.argv[1] == '--exe':
        process = await asyncio.create_subprocess_exec(
            cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={
                **os.environ,
                'MATLAB_PATH': r'C:\Program Files\MATLAB\R2025b',
                'MATLAB_WORKSPACE_DIR': r'C:\projects\matlabserver\matlab_workspace'
            }
        )
    else:
        # Add src to PYTHONPATH for module import
        env = os.environ.copy()
        env['PYTHONPATH'] = r'C:\projects\matlabserver\src' + (';' + env.get('PYTHONPATH', ''))
        env['MATLAB_PATH'] = r'C:\Program Files\MATLAB\R2025b'
        env['MATLAB_WORKSPACE_DIR'] = r'C:\projects\matlabserver\matlab_workspace'

        process = await asyncio.create_subprocess_exec(
            cmd, *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=r'C:\projects\matlabserver',
            env=env
        )

    print("\n=== MCP Server started ===\n", file=sys.stderr)

    # Create async streams
    reader = process.stdout
    writer = process.stdin

    try:
        # Step 1: Send initialize request (this is what Claude Desktop sends first)
        print("\n--- Step 1: Sending initialize request ---", file=sys.stderr)
        init_request = create_jsonrpc_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )
        await send_message(writer, init_request)

        # Wait for initialize response
        print("\n--- Waiting for initialize response ---", file=sys.stderr)
        response = await asyncio.wait_for(receive_message(reader), timeout=5.0)
        if response:
            print(f"Initialize response: {json.dumps(response, indent=2)}", file=sys.stderr)
        else:
            print("ERROR: No initialize response received!", file=sys.stderr)
            return

        # Step 2: Send initialized notification (required by protocol)
        print("\n--- Step 2: Sending initialized notification ---", file=sys.stderr)
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await send_message(writer, initialized_notification)

        # Give server a moment to process
        await asyncio.sleep(0.5)

        # Step 3: List available tools
        print("\n--- Step 3: Listing tools ---", file=sys.stderr)
        list_tools_request = create_jsonrpc_request("tools/list")
        await send_message(writer, list_tools_request)

        response = await asyncio.wait_for(receive_message(reader), timeout=5.0)
        if response:
            print(f"Tools list response: {json.dumps(response, indent=2)}", file=sys.stderr)

        # Step 4: Create a sine wave plot
        print("\n--- Step 4: Creating sine wave plot ---", file=sys.stderr)
        sine_wave_code = """
        % Create sine wave
        x = linspace(0, 4*pi, 1000);
        y = sin(x);

        % Create figure
        figure('Name', 'Sine Wave Test', 'NumberTitle', 'off');
        plot(x, y, 'b-', 'LineWidth', 2);
        grid on;
        xlabel('x');
        ylabel('sin(x)');
        title('Sine Wave from MCP Test');

        % Display message
        disp('Sine wave plot created successfully!');
        """

        execute_request = create_jsonrpc_request(
            "tools/call",
            {
                "name": "execute_matlab_code",
                "arguments": {
                    "code": sine_wave_code
                }
            }
        )
        await send_message(writer, execute_request)

        response = await asyncio.wait_for(receive_message(reader), timeout=10.0)
        if response:
            print(f"Execute response: {json.dumps(response, indent=2)}", file=sys.stderr)

        # Step 5: Export the figure to PNG
        print("\n--- Step 5: Exporting figure to PNG ---", file=sys.stderr)
        export_request = create_jsonrpc_request(
            "tools/call",
            {
                "name": "export_figure",
                "arguments": {
                    "filename": "sine_wave_test.png",
                    "format": "png",
                    "dpi": 150
                }
            }
        )
        await send_message(writer, export_request)

        response = await asyncio.wait_for(receive_message(reader), timeout=10.0)
        if response:
            print(f"Export response: {json.dumps(response, indent=2)}", file=sys.stderr)
            # Extract the file path from the response if available
            if response.get("result") and response["result"].get("content"):
                content = response["result"]["content"][0].get("text", "")
                print(f"\n--- Export result ---\n{content}", file=sys.stderr)

        # Step 6: Keep connection open briefly (simulating Claude Desktop behavior)
        print("\n--- Step 6: Keeping connection open (like Claude Desktop) ---", file=sys.stderr)
        await asyncio.sleep(2)

        # Step 7: Send another command
        print("\n--- Step 7: Sending second command ---", file=sys.stderr)
        execute_request2 = create_jsonrpc_request(
            "tools/call",
            {
                "name": "execute_matlab_code",
                "arguments": {
                    "code": "x = 1 + 1"
                }
            }
        )
        await send_message(writer, execute_request2)

        response = await asyncio.wait_for(receive_message(reader), timeout=10.0)
        if response:
            print(f"Second execute response: {json.dumps(response, indent=2)}", file=sys.stderr)

        print("\n=== Test completed successfully ===", file=sys.stderr)

    except asyncio.TimeoutError:
        print("\nERROR: Timeout waiting for response - server may be hung!", file=sys.stderr)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        # Clean shutdown
        print("\n--- Closing connection ---", file=sys.stderr)
        writer.close()
        await writer.wait_closed()

        # Terminate the process
        process.terminate()
        await asyncio.sleep(0.5)
        if process.returncode is None:
            process.kill()

        # Get any stderr output
        stderr_output = await process.stderr.read()
        if stderr_output:
            print(f"\nServer stderr output:\n{stderr_output.decode()}", file=sys.stderr)

if __name__ == "__main__":
    import os
    print(f"Python: {sys.version}", file=sys.stderr)
    print(f"Working directory: {os.getcwd()}", file=sys.stderr)
    print(f"Arguments: {sys.argv}", file=sys.stderr)

    # Run the test
    asyncio.run(test_mcp_server())