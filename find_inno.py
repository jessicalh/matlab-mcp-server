import os

paths_to_check = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    r"C:\Program Files\Inno Setup 5\ISCC.exe",
]

print("Looking for Inno Setup...")
for path in paths_to_check:
    if os.path.exists(path):
        print(f"FOUND: {path}")
    else:
        print(f"Not found: {path}")
