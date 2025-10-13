import subprocess
import os
import sys
import shutil
import webbrowser
import time
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

try:
    import psutil
except ImportError:
    print("psutil not found, installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

PYINSTALLER = "pyinstaller"
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PY = os.path.join(BASE_DIR, "font2c_lvgl.py")
APP_ISS = os.path.join(BASE_DIR, "Setup.iss")
ICON_FILE = os.path.join(BASE_DIR, "icons", "CentumTool.ico") # (Use branded Centum icon if available!)

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
    print_step(3, f"Building CentumConfigurationTool.exe executable")
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

class ThreadedHTTPServer:
    def __init__(self, host, port, directory):
        self.server = ThreadingHTTPServer(
            (host, port),
            lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=directory, **kwargs),
        )
    def start(self):
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()
    def stop(self):
        self.server.shutdown()
        self.server.server_close()

def create_download_page(output_folder, exe_name):
    html_path = os.path.join(output_folder, "index.html")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Download Centum Configuration Tool</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 2em; }}
            .download-link {{
                display: inline-block;
                background-color: #0078d7;
                color: white;
                padding: 1em 2em;
                text-decoration: none;
                border-radius: 6px;
                font-size: 1.2em;
            }}
            .download-link:hover {{
                background-color: #005a9e;
            }}
        </style>
    </head>
    <body>
        <h1>Centum Configuration Tool Installer</h1>
        <p>Click below to manually download the installer:</p>
        <a class="download-link" href="{exe_name}">Download Installer</a>
    </body>
    </html>
    """
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_path

def serve_localhost():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    html_path = create_download_page(OUTPUT_FOLDER, EXE_NAME)
    print_step(6, f"Serving {OUTPUT_FOLDER} on http://localhost:{SERVER_PORT}/")
    server = ThreadedHTTPServer("127.0.0.1", SERVER_PORT, OUTPUT_FOLDER)
    server.start()
    url = f"http://localhost:{SERVER_PORT}/index.html"
    print(f"Opening download page at {url}")
    webbrowser.open(url)
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop()

def main():
    print("\n" + "#" * 60)
    print("===== Centum Configuration Tool Build and Serve Script =====")
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
    serve_localhost()

if __name__ == "__main__":
    SERVER_PORT = 9000
    main()
