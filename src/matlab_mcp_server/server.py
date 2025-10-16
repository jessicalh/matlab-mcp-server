#!/usr/bin/env python3
"""MATLAB MCP Server - Main server implementation."""

import os
import sys
import asyncio
import json
from typing import Any, Optional
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Import our MATLAB wrapper
from matlab_engine_wrapper import MATLABEngineWrapper


# Global MATLAB engine instance
matlab_engine: Optional[MATLABEngineWrapper] = None


def get_matlab_engine() -> MATLABEngineWrapper:
    """Get or initialize MATLAB engine instance."""
    global matlab_engine

    if matlab_engine is None:
        matlab_path = os.getenv("MATLAB_PATH")
        matlab_engine = MATLABEngineWrapper(matlab_path)

        # Start the engine
        result = matlab_engine.start()
        if not result["success"]:
            raise RuntimeError(f"Failed to start MATLAB: {result.get('error', 'Unknown error')}")

    return matlab_engine


# Create MCP server instance
app = Server("matlab-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MATLAB tools."""
    return [
        Tool(
            name="execute_matlab_code",
            description="""Execute MATLAB code with full output capture including stdout, stderr, warnings, and errors.

            IMPORTANT: When plots/figures are created, they will automatically pop up in MATLAB GUI windows
            for immediate user interaction. Figures are automatically positioned on-screen in a cascade pattern
            to ensure they are visible and not off-screen.

            You do NOT need to manually export figures unless the user specifically requests saved image files.
            The figures will be displayed for the user to interact with directly in MATLAB.

            Returns all debugging information and metadata about figures created.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "MATLAB code to execute"
                    },
                    "capture_output": {
                        "type": "boolean",
                        "description": "Whether to capture output (default: true)",
                        "default": True
                    },
                    "position_figures": {
                        "type": "boolean",
                        "description": "Whether to auto-position new figures on screen (default: true)",
                        "default": True
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="get_workspace_variable",
            description="Retrieve a variable from the MATLAB workspace with its value and metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "variable_name": {
                        "type": "string",
                        "description": "Name of the variable to retrieve"
                    }
                },
                "required": ["variable_name"]
            }
        ),
        Tool(
            name="list_workspace",
            description="List all variables currently in the MATLAB workspace with their sizes and types.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="clear_workspace",
            description="Clear variables from the MATLAB workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "variables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of variable names to clear. If omitted, clears all variables."
                    }
                }
            }
        ),
        Tool(
            name="export_figure",
            description="Export a MATLAB figure to PNG, SVG, PDF, or EPS format with configurable resolution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "figure_handle": {
                        "type": "integer",
                        "description": "Figure handle number (omit for current figure)"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Output filename (auto-generated if omitted)"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "pdf", "eps", "jpg", "tiff"],
                        "description": "Export format",
                        "default": "png"
                    },
                    "dpi": {
                        "type": "integer",
                        "description": "Resolution in DPI (uses MATLAB_FIGURE_DPI env var if omitted)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="export_all_figures",
            description="Export all open MATLAB figures to files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "pdf", "eps"],
                        "description": "Export format for all figures",
                        "default": "png"
                    },
                    "dpi": {
                        "type": "integer",
                        "description": "Resolution in DPI"
                    }
                }
            }
        ),
        Tool(
            name="get_symbolic_latex",
            description="Convert a MATLAB symbolic expression to LaTeX format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Symbolic expression or variable name to convert"
                    }
                },
                "required": ["expression"]
            }
        ),
        Tool(
            name="save_matlab_script",
            description="Save MATLAB code to a .m file in the workspace directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "MATLAB code to save"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Filename (will add .m extension if needed)"
                    }
                },
                "required": ["code", "filename"]
            }
        ),
        Tool(
            name="set_project",
            description="Set the current project. Creates a directory in Documents/MATLAB_Projects/<project_name> and uses it for all output files for the session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project (will create/use directory with this name)"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="get_current_project",
            description="Get information about the current project, including the project name and output directory.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_projects",
            description="List all available projects in Documents/MATLAB_Projects directory.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="position_all_figures",
            description="Reposition all open MATLAB figure windows on screen using specified strategy (cascade or tile). Useful if figures are off-screen or overlapping.",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "enum": ["cascade", "tile"],
                        "description": "Positioning strategy to use (default: cascade)",
                        "default": "cascade"
                    }
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool execution requests."""
    try:
        engine = get_matlab_engine()

        if name == "execute_matlab_code":
            code = arguments["code"]
            capture_output = arguments.get("capture_output", True)
            position_figures = arguments.get("position_figures", True)
            validate = arguments.get("validate_results", True)
            save_script = arguments.get("save_script")

            result = engine.execute(
                code,
                capture_output=capture_output,
                auto_position_figures=position_figures,
                validate_results=validate,
                auto_save_script=save_script
            )

            # Format output for display
            output_parts = []

            if result.get("success"):
                # Check if there are warnings even though it "succeeded"
                if result.get("has_warnings"):
                    output_parts.append("⚠️  Execution completed with warnings\n")
                else:
                    output_parts.append("✓ Execution successful\n")

                # Display validation issues if any
                validation = result.get("validation", {})
                if validation.get("issues"):
                    output_parts.append("\n⚠️  Issues detected:\n")
                    for issue in validation["issues"]:
                        severity_emoji = {
                            "critical": "🔴",
                            "warning": "⚠️ ",
                            "info": "ℹ️ "
                        }.get(issue.get("severity", "info"), "•")
                        output_parts.append(f"  {severity_emoji} {issue['message']}\n")
                    output_parts.append("\n")

                # Display MATLAB warnings
                if validation.get("warnings"):
                    output_parts.append("MATLAB Warnings:\n")
                    for warn in validation["warnings"]:
                        output_parts.append(f"  • {warn['message']}\n")
                        if warn.get("id"):
                            output_parts.append(f"    (ID: {warn['id']})\n")
                    output_parts.append("\n")

                # Display figure information if figures were created
                if result.get("figures_created", 0) > 0:
                    fig_count = result["figures_created"]
                    output_parts.append(f"📊 {fig_count} figure(s) created and displayed in MATLAB GUI\n")

                    # Report on figure validation
                    fig_validations = validation.get("figures", [])
                    for i, fig_val in enumerate(fig_validations, 1):
                        if not fig_val.get("is_valid"):
                            output_parts.append(f"   ⚠️  Figure {i} appears to be blank or empty\n")
                            if fig_val.get("issues"):
                                for issue in fig_val["issues"]:
                                    output_parts.append(f"      - {issue}\n")
                        else:
                            plot_count = fig_val.get("plot_object_count", 0)
                            output_parts.append(f"   ✓ Figure {i} contains {plot_count} plot object(s)\n")

                    if result.get("figures_positioned"):
                        output_parts.append(f"   Positioned {result['figures_positioned']} figure(s) on screen\n")
                    output_parts.append("\n")

                # Display script save info
                if result.get("script_saved"):
                    output_parts.append(f"💾 Script saved: {result['script_saved']}\n\n")

                if result.get("stdout"):
                    output_parts.append(f"Output:\n{result['stdout']}\n")

                if result.get("stderr"):
                    output_parts.append(f"Warnings/Messages:\n{result['stderr']}\n")

                if not result.get("stdout") and not result.get("stderr") and result.get("figures_created", 0) == 0:
                    output_parts.append("(No output produced)\n")

            else:
                output_parts.append("✗ Execution failed\n")
                output_parts.append(f"Error: {result.get('error', 'Unknown error')}\n")

                # Display validation issues that caused failure
                validation = result.get("validation", {})
                if validation.get("issues"):
                    output_parts.append("\nCritical issues:\n")
                    for issue in validation["issues"]:
                        if issue.get("severity") == "critical":
                            output_parts.append(f"  🔴 {issue['message']}\n")

                if result.get("stdout"):
                    output_parts.append(f"\nOutput before error:\n{result['stdout']}\n")

                if result.get("stderr"):
                    output_parts.append(f"\nError details:\n{result['stderr']}\n")

            return [TextContent(type="text", text="".join(output_parts))]

        elif name == "get_workspace_variable":
            var_name = arguments["variable_name"]
            result = engine.get_variable(var_name)

            if result["success"]:
                output = f"Variable: {result['name']}\n"
                output += f"Type: {result['info'].get('class', 'unknown')}\n"
                output += f"Size: {result['info'].get('size', 'unknown')}\n"
                output += f"Value:\n{result['value']}\n"
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "list_workspace":
            result = engine.list_workspace()

            if result["success"]:
                output = "MATLAB Workspace Variables:\n\n"
                output += result["details"] if result["details"] else "Workspace is empty"

                if result["variables"]:
                    output += f"\n\nVariable names: {', '.join(result['variables'])}"
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "clear_workspace":
            variables = arguments.get("variables")
            result = engine.clear_workspace(variables)

            if result["success"]:
                if variables:
                    output = f"Cleared variables: {', '.join(variables)}"
                else:
                    output = "Cleared all workspace variables"
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "export_figure":
            figure_handle = arguments.get("figure_handle")
            filename = arguments.get("filename")
            format_type = arguments.get("format", "png")
            dpi = arguments.get("dpi")

            result = engine.export_figure(
                figure_handle=figure_handle,
                filename=filename,
                format=format_type,
                dpi=dpi
            )

            if result["success"]:
                output = f"Figure exported successfully:\n"
                output += f"Path: {result['path']}\n"
                output += f"Format: {result['format']}"

                # If it's an image format, we could optionally return the image
                # For now, just return the path
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "export_all_figures":
            format_type = arguments.get("format", "png")
            dpi = arguments.get("dpi")

            # Get list of open figures
            fig_result = engine.execute("fig_handles = get(groot, 'Children');", capture_output=False)

            if not fig_result["success"]:
                return [TextContent(type="text", text=f"Error getting figures: {fig_result['error']}")]

            # Get figure handles as a list
            try:
                fig_handles = engine.get_variable("fig_handles")
                if not fig_handles["success"] or not fig_handles.get("value"):
                    return [TextContent(type="text", text="No figures are currently open")]

                # Export each figure
                results = []
                handles = fig_handles["value"]

                # Handle both single figure and multiple figures
                if not hasattr(handles, '__iter__'):
                    handles = [handles]

                for i, handle in enumerate(handles):
                    result = engine.export_figure(
                        figure_handle=int(handle),
                        format=format_type,
                        dpi=dpi
                    )
                    results.append(result)

                # Format output
                output = f"Exported {len(results)} figure(s):\n\n"
                for i, result in enumerate(results, 1):
                    if result["success"]:
                        output += f"{i}. {result['path']}\n"
                    else:
                        output += f"{i}. Error: {result['error']}\n"

            except Exception as e:
                output = f"Error exporting figures: {str(e)}"

            return [TextContent(type="text", text=output)]

        elif name == "get_symbolic_latex":
            expression = arguments["expression"]
            result = engine.get_symbolic_latex(expression)

            if result["success"]:
                output = f"LaTeX representation of '{result['expression']}':\n\n"
                output += f"```latex\n{result['latex']}\n```"
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "save_matlab_script":
            code = arguments["code"]
            filename = arguments["filename"]

            result = engine.save_script(code, filename)

            if result["success"]:
                output = f"Script saved successfully:\n{result['path']}"
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "set_project":
            project_name = arguments["project_name"]
            result = engine.set_project(project_name)

            if result["success"]:
                output = f"✓ Project set to: {result['project_name']}\n"
                output += f"Output directory: {result['project_dir']}\n"
                output += f"\nAll files will be saved to this directory for the duration of the session."
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "get_current_project":
            result = engine.get_current_project()

            if result["success"]:
                if result.get("project_name"):
                    output = f"Current project: {result['project_name']}\n"
                    output += f"Project directory: {result['project_dir']}\n"
                    output += f"Workspace directory: {result['workspace_dir']}"
                else:
                    output = result.get("message", "No project currently set")
                    output += f"\nDefault workspace: {result['workspace_dir']}"
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "list_projects":
            result = engine.list_projects()

            if result["success"]:
                if result["projects"]:
                    output = f"Available projects in {result['projects_dir']}:\n\n"
                    for i, proj in enumerate(result["projects"], 1):
                        marker = " (current)" if proj == result.get("current_project") else ""
                        output += f"{i}. {proj}{marker}\n"
                else:
                    output = result.get("message", "No projects found")
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        elif name == "position_all_figures":
            strategy = arguments.get("strategy", "cascade")

            if strategy == "tile":
                result = engine._position_figures_tile()
            else:
                result = engine._position_figures_cascade()

            if result["success"]:
                fig_count = result.get("figures_positioned", 0)
                output = f"✓ Repositioned {fig_count} figure(s) using {strategy} strategy"
            else:
                output = f"Error: {result['error']}"

            return [TextContent(type="text", text=output)]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing tool '{name}': {str(e)}\n\nDetails: {type(e).__name__}"
        )]


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down MATLAB MCP Server...")
        if matlab_engine:
            matlab_engine.stop()
