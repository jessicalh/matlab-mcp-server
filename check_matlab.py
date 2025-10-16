import os

print("Checking MATLAB installations...")
print("R2024b exists:", os.path.exists("C:\\Program Files\\MATLAB\\R2024b"))
print("R2025b exists:", os.path.exists("C:\\Program Files\\MATLAB\\R2025b"))

if os.path.exists("C:\\Program Files\\MATLAB"):
    try:
        matlab_dirs = os.listdir("C:\\Program Files\\MATLAB")
        print("\nMATLAB installations found:")
        for d in matlab_dirs:
            print(f"  - {d}")
    except Exception as e:
        print(f"Error listing: {e}")
