import os
import subprocess

exe_path = os.path.join("dist", "font2c_lvgl.exe")

if os.path.exists(exe_path):
    print(f"Deleting existing executable: {exe_path}")
    os.remove(exe_path)

print("Building executable...")
subprocess.run(["pyinstaller", "--onefile", "--windowed", "font2c_lvgl.py"], check=True)
print("Build completed.")