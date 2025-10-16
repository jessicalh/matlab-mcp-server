#!/usr/bin/env python3
"""Direct test of MATLAB MCP Server without MCP Inspector."""

import sys
import os

# Set MATLAB_PATH before imports
os.environ["MATLAB_PATH"] = r"C:\Program Files\MATLAB\R2025b"

# Add src to path
sys.path.insert(0, r"C:\projects\matlabserver\src")

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("TEST 1: Import Modules")
    print("=" * 60)
    try:
        print("Importing MATLAB Engine Wrapper...")
        from matlab_mcp_server.matlab_engine_wrapper import MATLABEngineWrapper
        print("  [OK] MATLABEngineWrapper imported")

        print("Importing MCP Server...")
        from matlab_mcp_server import server
        print("  [OK] Server module imported")

        return True
    except Exception as e:
        print(f"  [FAIL] Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_engine_wrapper():
    """Test MATLAB Engine Wrapper can be instantiated."""
    print("\n" + "=" * 60)
    print("TEST 2: MATLAB Engine Wrapper")
    print("=" * 60)
    try:
        from matlab_mcp_server.matlab_engine_wrapper import MATLABEngineWrapper

        print("Creating wrapper instance...")
        wrapper = MATLABEngineWrapper(matlab_path=os.environ["MATLAB_PATH"])
        print("  [OK] Wrapper created")

        print("Starting MATLAB Engine...")
        result = wrapper.start()

        if result["success"]:
            print(f"  [OK] MATLAB Engine started")
            print(f"       Version: {result.get('matlab_version', 'unknown')}")

            # Test simple execution
            print("\nTesting simple execution...")
            exec_result = wrapper.execute("x = 1 + 1; disp(x);")

            if exec_result["success"]:
                print(f"  [OK] Execution successful")
                print(f"       Output: {exec_result.get('stdout', '').strip()}")
                print(f"       Figures created: {exec_result.get('figures_created', 0)}")
            else:
                print(f"  [FAIL] Execution failed: {exec_result.get('error')}")

            # Test figure creation
            print("\nTesting figure creation...")
            fig_result = wrapper.execute("x=0:0.1:2*pi; plot(x,sin(x)); title('Test');")

            if fig_result["success"]:
                print(f"  [OK] Figure creation successful")
                print(f"       Figures created: {fig_result.get('figures_created', 0)}")
                print(f"       Figures positioned: {fig_result.get('figures_positioned', 0)}")

                # Check validation
                validation = fig_result.get("validation", {})
                if validation.get("figures"):
                    for i, fig_val in enumerate(validation["figures"], 1):
                        is_valid = fig_val.get("is_valid", False)
                        status = "VALID" if is_valid else "BLANK"
                        print(f"       Figure {i}: {status}")
            else:
                print(f"  [FAIL] Figure creation failed: {fig_result.get('error')}")

            # Test blank figure detection
            print("\nTesting blank figure detection...")
            blank_result = wrapper.execute("figure();")

            if blank_result["success"] or blank_result.get("has_warnings"):
                validation = blank_result.get("validation", {})
                has_blank = any(
                    not fig.get("is_valid", True)
                    for fig in validation.get("figures", [])
                )
                if has_blank:
                    print(f"  [OK] Blank figure correctly detected")
                else:
                    print(f"  [WARN] Blank figure not detected (may be expected)")
            else:
                print(f"  [INFO] Result: {blank_result.get('error', 'Unknown')}")

            # Test warning detection (singular matrix)
            print("\nTesting critical warning detection...")
            warn_result = wrapper.execute("A = [1 2; 2 4]; b = [1; 2]; x = A\\b;")

            validation = warn_result.get("validation", {})
            if validation.get("warnings"):
                print(f"  [OK] Warnings detected:")
                for warn in validation["warnings"]:
                    print(f"       - [{warn.get('severity', 'unknown')}] {warn.get('message', '')[:80]}")
            else:
                print(f"  [INFO] No warnings captured (MATLAB version may vary)")

            # Cleanup
            print("\nStopping MATLAB Engine...")
            stop_result = wrapper.stop()
            if stop_result["success"]:
                print("  [OK] Engine stopped")
            else:
                print(f"  [WARN] Stop issue: {stop_result.get('message')}")

            return True
        else:
            print(f"  [FAIL] Failed to start: {result.get('error')}")
            if result.get("traceback"):
                print(f"\nTraceback:\n{result['traceback']}")
            return False

    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MATLAB MCP Server - Direct Testing")
    print("=" * 60)
    print(f"MATLAB Path: {os.environ.get('MATLAB_PATH')}")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Imports
    results.append(("Imports", test_imports()))

    # Test 2: Engine Wrapper
    results.append(("Engine Wrapper", test_engine_wrapper()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    print("=" * 60)

    # Check for log file
    if os.path.exists("matlab_mcp_server.log"):
        print("\nDetailed logs written to: matlab_mcp_server.log")

    # Exit code
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)


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
