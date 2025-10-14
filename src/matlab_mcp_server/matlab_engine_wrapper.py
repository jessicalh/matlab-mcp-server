"""Wrapper for MATLAB Engine API with comprehensive output capture."""

import io
import os
from typing import Dict, Any, Optional, Tuple
import matlab.engine


class MATLABEngineWrapper:
    """Wrapper for MATLAB Engine that captures all output and provides utility functions."""

    def __init__(self, matlab_path: Optional[str] = None):
        """Initialize MATLAB Engine.

        Args:
            matlab_path: Path to MATLAB installation (optional, uses system default if not provided)
        """
        self.matlab_path = matlab_path
        self.engine: Optional[matlab.engine.MatlabEngine] = None
        self.workspace_dir = os.getenv("MATLAB_WORKSPACE_DIR", "./matlab_workspace")
        self.figure_dpi = int(os.getenv("MATLAB_FIGURE_DPI", "300"))
        self.current_project: Optional[str] = None
        self.current_project_dir: Optional[str] = None

        # Create workspace directory if it doesn't exist
        os.makedirs(self.workspace_dir, exist_ok=True)

    def start(self) -> Dict[str, Any]:
        """Start MATLAB Engine session.

        Returns:
            Dict with status and message
        """
        try:
            if self.matlab_path:
                # Set MATLAB path if provided
                os.environ["MATLAB_PATH"] = self.matlab_path

            self.engine = matlab.engine.start_matlab()

            # Set up initial configuration
            self.engine.eval("format long;", nargout=0)  # Better numeric precision

            return {
                "success": True,
                "message": "MATLAB Engine started successfully",
                "matlab_version": self._get_matlab_version()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start MATLAB Engine: {str(e)}",
                "error": str(e)
            }

    def stop(self) -> Dict[str, Any]:
        """Stop MATLAB Engine session.

        Returns:
            Dict with status and message
        """
        try:
            if self.engine:
                self.engine.quit()
                self.engine = None
            return {"success": True, "message": "MATLAB Engine stopped"}
        except Exception as e:
            return {"success": False, "message": f"Error stopping engine: {str(e)}"}

    def is_running(self) -> bool:
        """Check if MATLAB Engine is running."""
        return self.engine is not None

    def execute(self, code: str, capture_output: bool = True) -> Dict[str, Any]:
        """Execute MATLAB code with comprehensive output capture.

        Args:
            code: MATLAB code to execute
            capture_output: Whether to capture stdout/stderr (default True)

        Returns:
            Dict containing:
                - success: bool
                - stdout: captured standard output
                - stderr: captured error output
                - error: error message if execution failed
                - warnings: any MATLAB warnings
        """
        if not self.is_running():
            return {
                "success": False,
                "error": "MATLAB Engine is not running. Call start() first."
            }

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            # Execute with output capture
            if capture_output:
                self.engine.eval(
                    code,
                    nargout=0,
                    stdout=stdout_buffer,
                    stderr=stderr_buffer
                )
            else:
                self.engine.eval(code, nargout=0)

            stdout_content = stdout_buffer.getvalue()
            stderr_content = stderr_buffer.getvalue()

            return {
                "success": True,
                "stdout": stdout_content,
                "stderr": stderr_content,
                "output": stdout_content  # Alias for convenience
            }

        except matlab.engine.MatlabExecutionError as e:
            # MATLAB execution error - code ran but had an error
            return {
                "success": False,
                "stdout": stdout_buffer.getvalue(),
                "stderr": stderr_buffer.getvalue(),
                "error": str(e),
                "error_type": "MatlabExecutionError"
            }
        except Exception as e:
            # Other Python/Engine errors
            return {
                "success": False,
                "stdout": stdout_buffer.getvalue(),
                "stderr": stderr_buffer.getvalue(),
                "error": str(e),
                "error_type": type(e).__name__
            }
        finally:
            stdout_buffer.close()
            stderr_buffer.close()

    def get_variable(self, var_name: str) -> Dict[str, Any]:
        """Get a variable from MATLAB workspace.

        Args:
            var_name: Name of the variable to retrieve

        Returns:
            Dict with variable value and metadata
        """
        if not self.is_running():
            return {"success": False, "error": "MATLAB Engine not running"}

        try:
            # Check if variable exists
            exists = self.engine.eval(f"exist('{var_name}', 'var')", nargout=1)
            if exists == 0:
                return {
                    "success": False,
                    "error": f"Variable '{var_name}' does not exist in workspace"
                }

            # Get variable value
            value = self.engine.workspace[var_name]

            # Get variable info
            var_info = self._get_variable_info(var_name)

            return {
                "success": True,
                "name": var_name,
                "value": value,
                "info": var_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get variable: {str(e)}"
            }

    def list_workspace(self) -> Dict[str, Any]:
        """List all variables in MATLAB workspace.

        Returns:
            Dict with list of variables and their properties
        """
        if not self.is_running():
            return {"success": False, "error": "MATLAB Engine not running"}

        try:
            # Get workspace info using 'whos'
            result = self.execute("whos;", capture_output=True)

            if not result["success"]:
                return result

            # Also get variable names as a list
            var_names_result = self.engine.eval("who()", nargout=1)

            return {
                "success": True,
                "variables": list(var_names_result) if var_names_result else [],
                "details": result["stdout"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list workspace: {str(e)}"
            }

    def clear_workspace(self, variables: Optional[list] = None) -> Dict[str, Any]:
        """Clear variables from MATLAB workspace.

        Args:
            variables: List of variable names to clear, or None to clear all

        Returns:
            Dict with status
        """
        if not self.is_running():
            return {"success": False, "error": "MATLAB Engine not running"}

        try:
            if variables:
                # Clear specific variables
                vars_str = " ".join(variables)
                result = self.execute(f"clear {vars_str};")
            else:
                # Clear all variables
                result = self.execute("clear all;")

            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to clear workspace: {str(e)}"
            }

    def export_figure(
        self,
        figure_handle: Optional[int] = None,
        filename: Optional[str] = None,
        format: str = "png",
        dpi: Optional[int] = None
    ) -> Dict[str, Any]:
        """Export MATLAB figure to file.

        Args:
            figure_handle: Figure handle number (None for current figure)
            filename: Output filename (auto-generated if None)
            format: Export format ('png', 'svg', 'pdf', 'eps')
            dpi: Resolution in DPI (uses default if None)

        Returns:
            Dict with export status and file path
        """
        if not self.is_running():
            return {"success": False, "error": "MATLAB Engine not running"}

        dpi = dpi or self.figure_dpi

        # Generate filename if not provided
        if not filename:
            import time
            timestamp = int(time.time())
            filename = f"figure_{timestamp}.{format}"

        # Ensure full path
        if not os.path.isabs(filename):
            filename = os.path.join(self.workspace_dir, filename)

        try:
            # Determine figure handle
            fig_ref = f"gcf" if figure_handle is None else f"figure({figure_handle})"

            # Use exportgraphics (modern MATLAB) or fallback to print
            export_code = f"""
            try
                % Try using exportgraphics (R2020a+)
                if strcmp('{format}', 'png') || strcmp('{format}', 'jpg') || strcmp('{format}', 'tiff')
                    exportgraphics({fig_ref}, '{filename}', 'Resolution', {dpi});
                else
                    % For vector formats
                    exportgraphics({fig_ref}, '{filename}', 'ContentType', 'vector');
                end
            catch
                % Fallback to print command for older MATLAB versions
                print({fig_ref}, '-d{format}', '-r{dpi}', '{filename}');
            end
            """

            result = self.execute(export_code)

            if result["success"] and os.path.exists(filename):
                return {
                    "success": True,
                    "message": f"Figure exported to {filename}",
                    "path": filename,
                    "format": format
                }
            else:
                return {
                    "success": False,
                    "error": "Export command executed but file not found",
                    "details": result
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to export figure: {str(e)}"
            }

    def get_symbolic_latex(self, expression: str) -> Dict[str, Any]:
        """Convert symbolic MATLAB expression to LaTeX.

        Args:
            expression: MATLAB symbolic expression or variable name

        Returns:
            Dict with LaTeX string
        """
        if not self.is_running():
            return {"success": False, "error": "MATLAB Engine not running"}

        try:
            # Create temporary variable to hold LaTeX output
            latex_code = f"""
            temp_latex_var = latex({expression});
            """

            result = self.execute(latex_code)

            if not result["success"]:
                return result

            # Retrieve the LaTeX string
            latex_str = self.engine.workspace["temp_latex_var"]

            # Clean up temporary variable
            self.execute("clear temp_latex_var;")

            return {
                "success": True,
                "latex": latex_str,
                "expression": expression
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate LaTeX: {str(e)}"
            }

    def save_script(self, code: str, filename: str) -> Dict[str, Any]:
        """Save MATLAB code to .m file.

        Args:
            code: MATLAB code to save
            filename: Filename (will add .m extension if needed)

        Returns:
            Dict with save status and file path
        """
        if not filename.endswith(".m"):
            filename += ".m"

        if not os.path.isabs(filename):
            filename = os.path.join(self.workspace_dir, filename)

        try:
            with open(filename, 'w') as f:
                f.write(code)

            return {
                "success": True,
                "message": f"Script saved to {filename}",
                "path": filename
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save script: {str(e)}"
            }

    def _get_matlab_version(self) -> str:
        """Get MATLAB version string."""
        try:
            version = self.engine.version(nargout=1)
            return str(version)
        except:
            return "unknown"

    def _get_variable_info(self, var_name: str) -> Dict[str, Any]:
        """Get detailed information about a variable.

        Args:
            var_name: Variable name

        Returns:
            Dict with variable metadata
        """
        try:
            # Get class/type
            var_class = self.engine.eval(f"class({var_name})", nargout=1)

            # Get size
            size_result = self.engine.eval(f"size({var_name})", nargout=1)

            return {
                "class": var_class,
                "size": list(size_result[0]) if hasattr(size_result, '__iter__') else [size_result]
            }
        except:
            return {}

    def set_project(self, project_name: str) -> Dict[str, Any]:
        """Set the current project and create project directory in Documents.

        Args:
            project_name: Name of the project

        Returns:
            Dict with status and project directory path
        """
        try:
            # Get user's Documents folder
            if os.name == 'nt':  # Windows
                documents = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents')
            else:  # macOS/Linux
                documents = os.path.join(os.path.expanduser('~'), 'Documents')

            # Create MATLAB_Projects folder if it doesn't exist
            matlab_projects_dir = os.path.join(documents, 'MATLAB_Projects')
            os.makedirs(matlab_projects_dir, exist_ok=True)

            # Create project-specific directory
            project_dir = os.path.join(matlab_projects_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)

            # Update current project
            self.current_project = project_name
            self.current_project_dir = project_dir
            self.workspace_dir = project_dir

            return {
                "success": True,
                "message": f"Project set to '{project_name}'",
                "project_name": project_name,
                "project_dir": project_dir
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to set project: {str(e)}"
            }

    def get_current_project(self) -> Dict[str, Any]:
        """Get information about the current project.

        Returns:
            Dict with current project information
        """
        if self.current_project:
            return {
                "success": True,
                "project_name": self.current_project,
                "project_dir": self.current_project_dir,
                "workspace_dir": self.workspace_dir
            }
        else:
            return {
                "success": True,
                "project_name": None,
                "message": "No project currently set",
                "workspace_dir": self.workspace_dir
            }

    def list_projects(self) -> Dict[str, Any]:
        """List all available projects in Documents/MATLAB_Projects.

        Returns:
            Dict with list of projects
        """
        try:
            # Get user's Documents folder
            if os.name == 'nt':  # Windows
                documents = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents')
            else:  # macOS/Linux
                documents = os.path.join(os.path.expanduser('~'), 'Documents')

            matlab_projects_dir = os.path.join(documents, 'MATLAB_Projects')

            # Check if projects directory exists
            if not os.path.exists(matlab_projects_dir):
                return {
                    "success": True,
                    "projects": [],
                    "message": "No projects found. Create one with set_project."
                }

            # List all subdirectories
            projects = [
                d for d in os.listdir(matlab_projects_dir)
                if os.path.isdir(os.path.join(matlab_projects_dir, d))
            ]

            return {
                "success": True,
                "projects": projects,
                "projects_dir": matlab_projects_dir,
                "current_project": self.current_project
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list projects: {str(e)}"
            }
