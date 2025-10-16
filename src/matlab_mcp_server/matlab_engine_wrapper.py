"""Wrapper for MATLAB Engine API with comprehensive output capture."""

import io
import math
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

        # Auto-positioning configuration
        self.auto_position_figures = os.getenv("MATLAB_AUTO_POSITION", "true").lower() == "true"
        self.positioning_strategy = os.getenv("MATLAB_POSITION_STRATEGY", "cascade")  # cascade, tile, center

        # Auto-save script configuration
        self.auto_save_scripts = os.getenv("MATLAB_AUTO_SAVE_SCRIPTS", "true").lower() == "true"
        self.auto_save_mode = os.getenv("MATLAB_AUTO_SAVE_MODE", "on_figures")  # always, on_figures, never

        # Validation configuration
        self.validate_results = os.getenv("MATLAB_VALIDATE_RESULTS", "true").lower() == "true"
        self.check_workspace_health = os.getenv("MATLAB_CHECK_WORKSPACE_HEALTH", "false").lower() == "true"
        self.strict_validation = os.getenv("MATLAB_STRICT_VALIDATION", "false").lower() == "true"

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

    def execute(
        self,
        code: str,
        capture_output: bool = True,
        auto_position_figures: bool = True,
        validate_results: bool = True,
        auto_save_script: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Execute MATLAB code with comprehensive output capture and validation.

        Args:
            code: MATLAB code to execute
            capture_output: Whether to capture stdout/stderr (default True)
            auto_position_figures: Whether to automatically position new figures (default True)
            validate_results: Whether to validate execution results (default True)
            auto_save_script: Whether to auto-save script. If None, uses configured setting

        Returns:
            Dict containing:
                - success: bool (True only if execution AND validation pass)
                - stdout: captured standard output
                - stderr: captured error output
                - error: error message if execution failed
                - warnings: MATLAB warnings captured
                - validation: validation results with severity levels
                - figures_created: number of new figures
                - figures_validated: validation results for each figure
                - new_figure_handles: list of new figure handles
                - figures_positioned: number of figures positioned (if auto_position_figures=True)
                - script_saved: path if script was saved
        """
        if not self.is_running():
            return {
                "success": False,
                "error": "MATLAB Engine is not running. Call start() first."
            }

        # Get figure handles BEFORE execution to detect new figures
        previous_figures = self._get_figure_handles()

        # Clear last warning BEFORE execution
        if validate_results:
            try:
                self.engine.eval("lastwarn('');", nargout=0)
            except Exception:
                pass  # Silently ignore if this fails

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

            # Detect new figures created during execution
            new_figures = self._detect_new_figures(previous_figures)

            result = {
                "success": True,
                "stdout": stdout_content,
                "stderr": stderr_content,
                "output": stdout_content,  # Alias for convenience
                "figures_created": len(new_figures),
                "new_figure_handles": new_figures
            }

            # Perform validation if requested
            if validate_results:
                validation = {"has_errors": False, "has_warnings": False, "warnings": [], "figures": [], "issues": []}

                # Check for MATLAB warnings
                warning_check = self._check_matlab_warnings()
                if warning_check["warnings"]:
                    validation["warnings"] = warning_check["warnings"]
                    validation["issues"].extend(warning_check["issues"])

                    if warning_check["has_critical"]:
                        validation["has_errors"] = True
                    else:
                        validation["has_warnings"] = True

                # Validate new figures
                if new_figures:
                    for fig_handle in new_figures:
                        fig_validation = self._validate_figure_content(fig_handle)
                        validation["figures"].append(fig_validation)

                        if not fig_validation["is_valid"]:
                            issue = {
                                "type": "blank_figure",
                                "severity": "warning",
                                "message": f"Figure {fig_handle} appears to be empty or blank",
                                "details": fig_validation
                            }
                            validation["issues"].append(issue)
                            validation["has_warnings"] = True

                result["validation"] = validation
                result["figures_validated"] = validation["figures"]

                # Downgrade success if validation finds critical issues
                if validation["has_errors"]:
                    result["success"] = False
                    result["error"] = "Execution completed but validation found critical issues"
                elif validation["has_warnings"]:
                    result["has_warnings"] = True

            # Auto-save script if configured
            save_script = auto_save_script if auto_save_script is not None else self.auto_save_scripts

            # Determine if we should save (always, or only when figures created)
            should_save = save_script and (
                self.auto_save_mode == "always" or
                (self.auto_save_mode == "on_figures" and len(new_figures) > 0)
            )

            if should_save:
                script_result = self._auto_save_script(
                    code,
                    figures_created=len(new_figures),
                    validation=result.get("validation")
                )
                if script_result.get("success"):
                    result["script_saved"] = script_result.get("path")

            # Auto-position new figures if requested
            if auto_position_figures and len(new_figures) > 0:
                position_result = self._position_figures_cascade()
                result["figures_positioned"] = position_result.get("figures_positioned", 0)

            return result

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

    def _get_figure_handles(self) -> list:
        """Get list of current figure handles.

        Returns:
            List of figure handles (empty list if none or error)
        """
        try:
            fig_handles = self.engine.eval("get(groot, 'Children')", nargout=1)
            if not fig_handles:
                return []
            if not hasattr(fig_handles, '__iter__'):
                return [fig_handles]
            return list(fig_handles)
        except Exception:
            return []

    def _detect_new_figures(self, previous_handles: list) -> list:
        """Detect newly created figures by comparing handle lists.

        Args:
            previous_handles: List of figure handles before code execution

        Returns:
            List of new figure handles
        """
        try:
            current_handles = self._get_figure_handles()

            # Convert to sets for comparison
            prev_set = set(previous_handles) if previous_handles else set()
            curr_set = set(current_handles)

            # Find new handles
            new_handles = list(curr_set - prev_set)
            return new_handles

        except Exception:
            return []

    def _position_figures_cascade(self) -> Dict[str, Any]:
        """Position all open figures in a cascade pattern on the primary screen.

        Returns:
            Dict with success status and number of figures positioned
        """
        if not self.is_running():
            return {"success": False, "error": "Engine not running"}

        try:
            # Get screen dimensions
            screen_size = self.engine.eval("get(0, 'ScreenSize')", nargout=1)
            # screen_size = [left, bottom, width, height]
            screen_width = int(screen_size[2])
            screen_height = int(screen_size[3])

            # Get all figure handles
            fig_handles = self._get_figure_handles()

            if not fig_handles:
                return {"success": True, "figures_positioned": 0}

            # Default figure size (can be customized)
            fig_width = min(800, int(screen_width * 0.6))
            fig_height = min(600, int(screen_height * 0.6))

            # Cascade offset
            cascade_offset = 40

            # Starting position (with margin from edges)
            start_x = 50
            start_y = screen_height - fig_height - 100  # From top of screen

            positioned_count = 0
            for i, fig_handle in enumerate(fig_handles):
                # Calculate cascade position
                x = start_x + (i * cascade_offset)
                y = start_y - (i * cascade_offset)

                # Reset cascade if going off screen
                if (x + fig_width > screen_width - 50) or (y < 50):
                    x = start_x
                    y = start_y

                # Set figure position
                # Note: MATLAB Position is [left, bottom, width, height]
                position_cmd = f"set({fig_handle}, 'Position', [{x}, {y}, {fig_width}, {fig_height}]);"
                self.engine.eval(position_cmd, nargout=0)
                positioned_count += 1

            return {
                "success": True,
                "figures_positioned": positioned_count,
                "strategy": "cascade"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to position figures: {str(e)}"
            }

    def _get_monitor_info(self) -> Dict[str, Any]:
        """Get information about all monitors.

        Returns:
            Dict with monitor information
        """
        try:
            # Get monitor positions
            monitor_pos = self.engine.eval("get(0, 'MonitorPositions')", nargout=1)

            # Convert to list of monitor info
            if len(monitor_pos.shape) == 1:
                # Single monitor
                monitors = [{
                    "left": int(monitor_pos[0]),
                    "bottom": int(monitor_pos[1]),
                    "width": int(monitor_pos[2]),
                    "height": int(monitor_pos[3]),
                    "is_primary": True
                }]
            else:
                # Multiple monitors
                monitors = []
                for i in range(monitor_pos.shape[0]):
                    monitors.append({
                        "left": int(monitor_pos[i][0]),
                        "bottom": int(monitor_pos[i][1]),
                        "width": int(monitor_pos[i][2]),
                        "height": int(monitor_pos[i][3]),
                        "is_primary": (i == 0)  # First monitor is primary
                    })

            return {
                "success": True,
                "monitor_count": len(monitors),
                "monitors": monitors
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get monitor info: {str(e)}"
            }

    def _position_figures_tile(self, monitor_index: int = 0) -> Dict[str, Any]:
        """Position figures in a tile pattern on specified monitor.

        Args:
            monitor_index: Which monitor to use (0 = primary)

        Returns:
            Dict with positioning results
        """
        try:
            # Get monitor info
            monitor_info = self._get_monitor_info()
            if not monitor_info["success"]:
                return monitor_info

            monitors = monitor_info["monitors"]
            if monitor_index >= len(monitors):
                monitor_index = 0  # Fall back to primary

            monitor = monitors[monitor_index]

            # Get figures
            fig_handles = self._get_figure_handles()
            if not fig_handles:
                return {"success": True, "figures_positioned": 0}

            num_figs = len(fig_handles)

            # Calculate grid layout
            cols = int(math.ceil(math.sqrt(num_figs)))
            rows = int(math.ceil(num_figs / cols))

            # Calculate figure sizes
            margin = 10
            usable_width = monitor["width"] - (cols + 1) * margin
            usable_height = monitor["height"] - (rows + 1) * margin - 100  # Leave room for taskbar

            fig_width = usable_width // cols
            fig_height = usable_height // rows

            # Position figures in grid
            for i, fig_handle in enumerate(fig_handles):
                row = i // cols
                col = i % cols

                x = monitor["left"] + margin + col * (fig_width + margin)
                y = monitor["bottom"] + monitor["height"] - (row + 1) * (fig_height + margin) - 100

                position_cmd = f"set({fig_handle}, 'Position', [{x}, {y}, {fig_width}, {fig_height}]);"
                self.engine.eval(position_cmd, nargout=0)

            return {
                "success": True,
                "figures_positioned": num_figs,
                "strategy": "tile",
                "monitor": monitor_index
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to tile figures: {str(e)}"
            }

    def _check_matlab_warnings(self) -> Dict[str, Any]:
        """Check for MATLAB warnings using lastwarn.

        Returns:
            Dict containing:
                - warnings: list of warning dicts with message and ID
                - has_critical: bool - whether any critical warnings found
                - issues: list of issue dicts for validation system
        """
        try:
            # Get last warning message and ID
            self.engine.eval("[warnMsg, warnId] = lastwarn;", nargout=0)
            warn_msg = self.engine.workspace.get("warnMsg", "")
            warn_id = self.engine.workspace.get("warnId", "")

            warnings = []
            issues = []
            has_critical = False

            if warn_msg and warn_msg.strip():
                # Categorize warning severity
                severity, is_critical = self._classify_warning_severity(warn_msg, warn_id)

                warning_entry = {
                    "message": warn_msg,
                    "id": warn_id,
                    "severity": severity
                }
                warnings.append(warning_entry)

                if is_critical:
                    has_critical = True

                # Create issue entry
                issues.append({
                    "type": "matlab_warning",
                    "severity": severity,
                    "message": warn_msg,
                    "warning_id": warn_id
                })

            return {
                "warnings": warnings,
                "has_critical": has_critical,
                "issues": issues
            }

        except Exception as e:
            return {
                "warnings": [],
                "has_critical": False,
                "issues": [{
                    "type": "warning_check_failed",
                    "severity": "info",
                    "message": f"Could not check warnings: {str(e)}"
                }]
            }

    def _classify_warning_severity(self, warn_msg: str, warn_id: str) -> tuple:
        """Classify warning severity based on message and ID.

        Args:
            warn_msg: Warning message text
            warn_id: Warning identifier

        Returns:
            Tuple of (severity_level, is_critical)
            severity_level: 'critical', 'warning', 'info'
            is_critical: bool - whether this should cause success=False
        """
        warn_msg_lower = warn_msg.lower()

        # Critical warnings that indicate results are likely invalid
        critical_keywords = [
            "singular",
            "rank deficient",
            "badly scaled",
            "ill-conditioned",
            "not positive definite"
        ]

        critical_ids = [
            "MATLAB:singularMatrix",
            "MATLAB:nearlySingularMatrix",
            "MATLAB:illConditionedMatrix",
            "MATLAB:rankDeficientMatrix"
        ]

        # Check for critical conditions
        for keyword in critical_keywords:
            if keyword in warn_msg_lower:
                return ("critical", True)

        if warn_id in critical_ids:
            return ("critical", True)

        # Non-critical but important warnings
        warning_keywords = [
            "divide by zero",
            "imaginary parts",
            "negative",
            "overflow",
            "underflow"
        ]

        for keyword in warning_keywords:
            if keyword in warn_msg_lower:
                return ("warning", False)

        # Default to info level
        return ("info", False)

    def _validate_figure_content(self, fig_handle) -> Dict[str, Any]:
        """Check if a figure contains actual plot content or is blank.

        Args:
            fig_handle: MATLAB figure handle

        Returns:
            Dict containing:
                - is_valid: bool - whether figure has content
                - has_axes: bool - whether figure has axes
                - axes_count: int - number of axes in figure
                - plot_object_count: int - total plot objects across all axes
                - details: dict with per-axes information
                - issues: list of issues found
        """
        try:
            # Check if figure has any axes
            self.engine.eval(
                f"axesHandles = findobj({fig_handle}, 'type', 'axes');",
                nargout=0
            )
            axes_handles = self.engine.workspace.get("axesHandles", [])

            # Convert to list
            if not hasattr(axes_handles, '__iter__'):
                axes_handles = [axes_handles] if axes_handles else []

            has_axes = len(axes_handles) > 0

            if not has_axes:
                return {
                    "is_valid": False,
                    "has_axes": False,
                    "axes_count": 0,
                    "plot_object_count": 0,
                    "details": {},
                    "issues": ["Figure has no axes"]
                }

            # Check each axes for plot objects
            total_plot_objects = 0
            axes_details = []
            axes_issues = []

            for i, ax_handle in enumerate(axes_handles):
                # Count children in this axes
                children_count = self.engine.eval(
                    f"numel(get({ax_handle}, 'Children'))",
                    nargout=1
                )

                # Get types of plot objects
                self.engine.eval(
                    f"""
                    ch = get({ax_handle}, 'Children');
                    if isempty(ch)
                        types = {{}};
                    else
                        types = get(ch, 'Type');
                        if ~iscell(types)
                            types = {{types}};
                        end
                    end
                    """,
                    nargout=0
                )
                plot_types_list = self.engine.workspace.get("types", [])

                axes_info = {
                    "axes_index": i,
                    "children_count": int(children_count),
                    "plot_types": list(plot_types_list) if plot_types_list else []
                }
                axes_details.append(axes_info)

                total_plot_objects += int(children_count)

                # Check if axes is empty
                if int(children_count) == 0:
                    axes_issues.append(f"Axes {i+1} is empty (no plot objects)")

            # Determine if figure is valid
            # A figure is valid if it has at least one axes with at least one plot object
            is_valid = total_plot_objects > 0

            return {
                "is_valid": is_valid,
                "has_axes": True,
                "axes_count": len(axes_handles),
                "plot_object_count": total_plot_objects,
                "details": axes_details,
                "issues": axes_issues if not is_valid else []
            }

        except Exception as e:
            return {
                "is_valid": True,  # Assume valid if we can't check (fail open)
                "has_axes": None,
                "axes_count": None,
                "plot_object_count": None,
                "details": {},
                "issues": [f"Could not validate figure: {str(e)}"]
            }

    def _check_workspace_health(self) -> Dict[str, Any]:
        """Check workspace for common problematic values (NaN, Inf, empty arrays).

        Returns:
            Dict containing:
                - has_issues: bool
                - has_critical: bool
                - issues: list of issue dicts
                - variables_checked: int
        """
        try:
            # Get list of variables in workspace
            var_names_result = self.engine.eval("who()", nargout=1)
            var_names = list(var_names_result) if var_names_result else []

            issues = []
            has_critical = False

            # Check a subset of variables (don't check everything to avoid performance issues)
            # Focus on recently created/modified variables
            for var_name in var_names[:10]:  # Limit to first 10 variables
                try:
                    # Check if variable contains NaN
                    has_nan = self.engine.eval(
                        f"any(isnan({var_name})(:))",
                        nargout=1
                    )

                    # Check if variable contains Inf
                    has_inf = self.engine.eval(
                        f"any(isinf({var_name})(:))",
                        nargout=1
                    )

                    # Check if variable is empty
                    is_empty = self.engine.eval(
                        f"isempty({var_name})",
                        nargout=1
                    )

                    if has_nan:
                        issues.append({
                            "type": "nan_detected",
                            "severity": "warning",
                            "message": f"Variable '{var_name}' contains NaN values",
                            "variable": var_name
                        })

                    if has_inf:
                        issues.append({
                            "type": "inf_detected",
                            "severity": "warning",
                            "message": f"Variable '{var_name}' contains Inf values",
                            "variable": var_name
                        })

                    if is_empty:
                        issues.append({
                            "type": "empty_variable",
                            "severity": "info",
                            "message": f"Variable '{var_name}' is empty",
                            "variable": var_name
                        })

                except Exception:
                    # Skip variables that can't be checked (might be non-numeric types)
                    continue

            return {
                "has_issues": len(issues) > 0,
                "has_critical": has_critical,
                "issues": issues,
                "variables_checked": len(var_names)
            }

        except Exception as e:
            return {
                "has_issues": False,
                "has_critical": False,
                "issues": [],
                "variables_checked": 0
            }

    def _auto_save_script(
        self,
        code: str,
        figures_created: int = 0,
        validation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Automatically save a script to the scripts directory with metadata.

        Args:
            code: MATLAB code to save
            figures_created: Number of figures created by this script
            validation: Validation results to include in header

        Returns:
            Dict with save status and file path
        """
        from datetime import datetime

        try:
            # Create scripts subdirectory
            scripts_dir = os.path.join(self.workspace_dir, "scripts")
            os.makedirs(scripts_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"script_{timestamp}.m"
            filepath = os.path.join(scripts_dir, filename)

            # Build comprehensive header
            header_lines = [
                "% Auto-saved MATLAB script",
                f"% Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"% Figures created: {figures_created}",
                f"% Project: {self.current_project or 'None'}",
            ]

            # Add validation info if available
            if validation:
                if validation.get("warnings"):
                    header_lines.append("%")
                    header_lines.append("% MATLAB Warnings:")
                    for warn in validation["warnings"]:
                        header_lines.append(f"%   - {warn['message']}")

                if validation.get("issues"):
                    header_lines.append("%")
                    header_lines.append("% Issues detected:")
                    for issue in validation["issues"]:
                        severity = issue.get("severity", "info").upper()
                        header_lines.append(f"%   [{severity}] {issue['message']}")

            header_lines.append("%")
            header_lines.append("")
            header = "\n".join(header_lines) + "\n"

            with open(filepath, 'w') as f:
                f.write(header)
                f.write(code)

            return {
                "success": True,
                "path": filepath,
                "message": f"Script auto-saved to {filepath}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to auto-save script: {str(e)}"
            }

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
