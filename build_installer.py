import subprocess
import sys
import importlib
import os
import shutil
import webbrowser
import requests
import psutil

try:
    from tkinter import filedialog, Tk
except ImportError:
    print("Tkinter is not installed. Please install it.")
    sys.exit(1)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def check_and_install_modules(required_modules):
    for mod_name, pkg_name in required_modules.items():
        try:
            importlib.import_module(mod_name)
        except ImportError:
            print(f"Module '{mod_name}' not found. Installing {pkg_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
            print(f"Module '{mod_name}' installed!")

required_modules = {
    "psutil": "psutil",
    "requests": "requests"
}
check_and_install_modules(required_modules)

PYINSTALLER = "pyinstaller"
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PY = os.path.join(BASE_DIR, "font2c_lvgl.py")
APP_ISS = os.path.join(BASE_DIR, "Setup.iss")
ICON_FILE = resource_path(os.path.join("icons", "CentumTool.ico"))
DIST_FOLDER = os.path.join(BASE_DIR, "dist")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "Output")
EXE_NAME = "CentumConfigurationTool.exe"
SERVER_PORT = 9000

def print_step(step_num, description):
    print("\n" + "*" * 60)
    print(f"Step {step_num}: {description}")
    print("*" * 60 + "\n")

def remove_folder_if_exists(folder_path):
    if os.path.exists(folder_path):
        print_step("Cleanup", f"Removing folder: {folder_path}")
        shutil.rmtree(folder_path)

def check_and_install_pyinstaller():
    print_step(1, "Checking if PyInstaller is installed...")
    try:
        subprocess.run([PYINSTALLER, "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("PyInstaller is already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Installing with pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

def check_iscc():
    print_step(2, "Checking for Inno Setup Compiler...")
    if not os.path.exists(ISCC_PATH):
        print(f"Error: Inno Setup Compiler not found at {ISCC_PATH}. Please install it.")
        sys.exit(1)
    else:
        print("Inno Setup Compiler found.")

def build_exe(icon_path):
    remove_folder_if_exists(DIST_FOLDER)
    remove_folder_if_exists(OUTPUT_FOLDER)
    print_step(3, f"Building {EXE_NAME} executable")
    cmd = [
        PYINSTALLER,
        "--onefile",
        "--windowed",  # Prevents terminal window pop-up during GUI app run
        f"--icon={icon_path}",
        APP_PY,
        "--name=CentumConfigurationTool",
        f"--distpath={DIST_FOLDER}",
        "--clean",
        "--add-data", f"icons{os.pathsep}icons"  # Bundle icons folder
    ]
    subprocess.run(cmd, check=True)
    exe_path = os.path.join(DIST_FOLDER, EXE_NAME)
    if not os.path.exists(exe_path):
        print(f"Error: EXE {exe_path} not created!")
        sys.exit(1)
    print(f"EXE built successfully at {exe_path}")
    return exe_path

def kill_running_processes(exe_name):
    print_step(4, f"Checking for running {exe_name} processes to terminate...")
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == exe_name.lower():
                print(f"Terminating process PID={proc.pid} ({proc.info['name']})")
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def run_installer_compiler():
    print_step(5, f"Running Inno Setup Compiler on {APP_ISS}")
    iss_dir = os.path.dirname(APP_ISS)
    subprocess.run([ISCC_PATH, APP_ISS], check=True, cwd=iss_dir)
    print("Installer created successfully.")

def ask_save_location(default_filename):
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # Keep dialog on top
    root.update()
    file_path = filedialog.asksaveasfilename(
        parent=root,
        title="Save EXE As",
        defaultextension=".exe",
        initialfile=default_filename,
        filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
    )
    root.destroy()
    return file_path

def main():
    print("\n" + "#" * 60)
    print("===== Centum Configuration Tool Build Script =====")
    print("#" * 60 + "\n")

    if not os.path.exists(APP_PY):
        print(f"App Python file not found: {APP_PY}")
        sys.exit(1)
    if not os.path.exists(resource_path(os.path.join('icons', 'CentumTool.ico'))):
        print(f"Icon file not found: {ICON_FILE}")
        sys.exit(1)

    check_and_install_pyinstaller()
    check_iscc()

    exe_path = build_exe(resource_path(os.path.join('icons', 'CentumTool.ico')))
    kill_running_processes(EXE_NAME)

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    exe_output_path = os.path.join(OUTPUT_FOLDER, EXE_NAME)
    shutil.copyfile(exe_path, exe_output_path)

    run_installer_compiler()

    print_step("Save", "Please select where to save your EXE file.")
    save_path = ask_save_location(EXE_NAME)

    if save_path:
        shutil.copyfile(exe_output_path, save_path)
        print(f"EXE saved to: {save_path}")
        webbrowser.open(f"file://{save_path}")
    else:
        print("No save location selected. Exiting.")

if __name__ == "__main__":
    SERVER_PORT = 9000
    main()
