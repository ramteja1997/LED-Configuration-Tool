import subprocess
import sys
import importlib

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

import os
import shutil
import webbrowser
import time
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import requests
import psutil

PYINSTALLER = "pyinstaller"
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PY = os.path.join(BASE_DIR, "font2c_lvgl.py")
APP_ISS = os.path.join(BASE_DIR, "Setup.iss")
ICON_FILE = os.path.join(BASE_DIR, "icons", "CentumTool.ico")

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
        "--windowed",
        f"--icon={icon_path}",
        APP_PY,
        "--name=CentumConfigurationTool",
        f"--distpath={DIST_FOLDER}",
        "--clean",
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

def upload_to_gofile(filepath):
    print_step("Upload", f"Uploading {filepath} to gofile.io...")
    upload_url = "https://store9.gofile.io/uploadFile"
    with open(filepath, 'rb') as f:
        files = {'file': (os.path.basename(filepath), f)}
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    data = response.json()
    print(f"Response data received: {data}")
    if data.get("status") == "ok":
        download_link = data["data"].get("downloadPage")
        print(f"Upload succeeded. Download page: {download_link}")
        return download_link
    else:
        print(f"Upload failed with response: {data}")
        return None

def main():
    print("\n" + "#" * 60)
    print("===== Centum Configuration Tool Build and Upload Script =====")
    print("#" * 60 + "\n")

    if not os.path.exists(APP_PY):
        print(f"App Python file not found: {APP_PY}")
        sys.exit(1)
    if not os.path.exists(ICON_FILE):
        print(f"Icon file not found: {ICON_FILE}")
        sys.exit(1)

    check_and_install_pyinstaller()
    check_iscc()

    exe_path = build_exe(ICON_FILE)
    kill_running_processes(EXE_NAME)

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    exe_output_path = os.path.join(OUTPUT_FOLDER, EXE_NAME)
    shutil.copyfile(exe_path, exe_output_path)

    run_installer_compiler()

    https_link = upload_to_gofile(exe_output_path)
    if https_link:
        print(f"\nYou can share this universal download link:\n{https_link}")
        webbrowser.open(https_link)
    else:
        print("Failed to upload installer to gofile.io.")

if __name__ == "__main__":
    SERVER_PORT = 9000
    main()
