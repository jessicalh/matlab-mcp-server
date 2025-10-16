#!/usr/bin/env python3
"""Test figure detection with R2025b."""

import sys
import os

os.environ["MATLAB_PATH"] = r"C:\Program Files\MATLAB\R2025b"
sys.path.insert(0, r"C:\projects\matlabserver\src")

from matlab_mcp_server.matlab_engine_wrapper import MATLABEngineWrapper

def test_figure_detection():
    """Test figure detection mechanisms."""
    print("="*60)
    print("Figure Detection Diagnostic Test")
    print("="*60)

    wrapper = MATLABEngineWrapper(os.environ["MATLAB_PATH"])
    result = wrapper.start()

    if not result["success"]:
        print(f"Failed to start MATLAB: {result['error']}")
        return

    print(f"MATLAB started: {result['matlab_version']}\n")

    # Test 1: Get initial figure handles
    print("TEST 1: Check initial state")
    initial_handles = wrapper._get_figure_handles()
    print(f"  Initial figure handles: {initial_handles}")

    # Test 2: Create a figure manually and check
    print("\nTEST 2: Create figure with figure() command")
    wrapper.engine.eval("f1 = figure();", nargout=0)
    handles_after_fig = wrapper._get_figure_handles()
    print(f"  Handles after figure(): {handles_after_fig}")
    print(f"  New handles: {set(handles_after_fig) - set(initial_handles)}")

    # Test 3: Create a plot and check
    print("\nTEST 3: Create plot")
    wrapper.engine.eval("f2 = figure(); plot([1,2,3], [1,4,9]);", nargout=0)
    handles_after_plot = wrapper._get_figure_handles()
    print(f"  Handles after plot: {handles_after_plot}")
    print(f"  New handles: {set(handles_after_plot) - set(handles_after_fig)}")

    # Test 4: Check groot.Children directly
    print("\nTEST 4: Check groot.Children directly")
    wrapper.engine.eval("groot_children = get(groot, 'Children');", nargout=0)
    groot_children = wrapper.engine.workspace.get("groot_children", None)
    print(f"  groot.Children value: {groot_children}")
    print(f"  Type: {type(groot_children)}")
    if groot_children is not None:
        if hasattr(groot_children, '__iter__'):
            print(f"  Length: {len(groot_children)}")
            print(f"  Items: {list(groot_children)}")
        else:
            print(f"  Single value: {groot_children}")

    # Test 5: Use findobj
    print("\nTEST 5: Use findobj to find figures")
    wrapper.engine.eval("all_figs = findobj('Type', 'figure');", nargout=0)
    all_figs = wrapper.engine.workspace.get("all_figs", None)
    print(f"  findobj figures: {all_figs}")
    print(f"  Type: {type(all_figs)}")

    # Test 6: Check if figures are valid
    if handles_after_plot:
        print("\nTEST 6: Validate figure content")
        for i, handle in enumerate(handles_after_plot, 1):
            print(f"\n  Figure {i} (handle {handle}):")
            validation = wrapper._validate_figure_content(handle)
            print(f"    Valid: {validation.get('is_valid')}")
            print(f"    Has axes: {validation.get('has_axes')}")
            print(f"    Axes count: {validation.get('axes_count')}")
            print(f"    Plot objects: {validation.get('plot_object_count')}")
            if validation.get('issues'):
                print(f"    Issues: {validation['issues']}")

    # Test 7: Test execution() method's figure detection
    print("\nTEST 7: Test execute() method figure detection")
    exec_result = wrapper.execute("f3 = figure(); x=0:0.1:2*pi; plot(x,sin(x));")
    print(f"  figures_created: {exec_result.get('figures_created')}")
    print(f"  new_figure_handles: {exec_result.get('new_figure_handles')}")

    # Cleanup
    wrapper.stop()
    print("\n" + "="*60)
    print("Test complete")
    print("="*60)

if __name__ == "__main__":
    test_figure_detection()
