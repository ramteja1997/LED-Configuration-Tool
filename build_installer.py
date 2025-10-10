import subprocess
import os
import sys
import shutil
import threading
import http.server
import socketserver
import webbrowser
import psutil
import importlib

# ==========================================================
# CONFIGURATION — All paths are now absolute (portable build)
# ==========================================================
PYINSTALLER = "pyinstaller"
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# Get absolute base directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define all important paths relative to BASE_DIR
APP_PY = os.path.join(BASE_DIR, "font2c_lvgl.py")
APP_ISS = os.path.join(BASE_DIR, "Setup.iss")
ICON_FILE = os.path.join(BASE_DIR, "icons", "LVGL_FontGen.ico")
DIST_FOLDER = os.path.join(BASE_DIR, "dist")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "Output")

INSTALLER_FILENAME = "LVGLFontGenerator_Installer.exe"
INSTALL_DIR = os.path.join(
    os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    "LVGLFontGenerator"
)
PORT = 8000

# ==========================================================
# Dependency check and install
# ==========================================================
def check_and_install_modules(required_modules):
    for module_name, install_name in required_modules.items():
        try:
            importlib.import_module(module_name)
            print(f"Module '{module_name}' is already installed.")
        except ImportError:
            print(f"Module '{module_name}' not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", install_name], check=True)
            print(f"Module '{module_name}' installed successfully.")

# List required modules here (module_name: pip_package_name)

required_modules = {
    "psutil": "psutil",
    "freetype": "freetype-py",
    # No need to include 'tkinter', 'os', 'sys', 'webbrowser' since they're standard
}

# ==========================================================
# Utility functions
# ==========================================================
def print_step(step_num, description):
    print("\n" + "*" * 60)
    print(f"Step {step_num}: {description}")
    print("*" * 60 + "\n")

def check_and_install_pyinstaller():
    print_step(1, "Checking if PyInstaller is installed...")
    try:
        subprocess.run([PYINSTALLER, "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("PyInstaller is already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Installing with pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("PyInstaller installed successfully.")

def check_iscc():
    print_step(2, "Checking for Inno Setup Compiler...")
    if not os.path.exists(ISCC_PATH):
        print(f"Error: Inno Setup Compiler not found at {ISCC_PATH}. Please install it.")
        sys.exit(1)
    else:
        print("Inno Setup Compiler found.")

def delete_existing_exe(exe_name):
    exe_path = os.path.join(DIST_FOLDER, exe_name)
    if os.path.exists(exe_path):
        print_step(3, f"Deleting existing EXE: {exe_path}")
        os.remove(exe_path)
    else:
        print_step(3, f"No existing EXE to delete at {exe_path}")
    return exe_path

def build_exe(icon_path):
    exe_name = os.path.basename(APP_PY).replace(".py", ".exe")
    exe_path = delete_existing_exe(exe_name)
    print_step(4, f"Building executable: {exe_name}")
    cmd = [
        PYINSTALLER,
        "--onefile",
        "--windowed",
        f"--icon={icon_path}",
        APP_PY,
        f"--distpath={DIST_FOLDER}",
        "--clean",
    ]
    subprocess.run(cmd, check=True)
    exe_path = os.path.join(DIST_FOLDER, exe_name)
    if not os.path.exists(exe_path):
        print(f"Error: EXE {exe_path} not created!")
        return None
    print(f"EXE built successfully at {exe_path}")
    return exe_path

def kill_font2c_processes():
    print_step(5, "Checking for running LVGL Font Generator processes to terminate...")
    killed_any = False
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == 'font2c_lvgl.exe':
                print(f"Terminating process PID={proc.pid} ({proc.info['name']})")
                proc.terminate()
                killed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if not killed_any:
        print("No running font2c_lvgl.exe processes found.")

def run_uninstaller_and_clean():
    uninstaller_path = os.path.join(INSTALL_DIR, "unins000.exe")
    if os.path.exists(uninstaller_path):
        print_step(6, f"Running uninstaller at: {uninstaller_path}")
        try:
            subprocess.run([uninstaller_path, "/VERYSILENT", "/NORESTART"], check=True)
            print("Uninstalled previous version.")
            return
        except subprocess.CalledProcessError:
            print("Uninstaller failed; attempting manual delete.")

    installed_exe = os.path.join(INSTALL_DIR, "font2c_lvgl.exe")
    if os.path.exists(installed_exe):
        print_step("6a", f"Deleting installed EXE manually: {installed_exe}")
        try:
            os.remove(installed_exe)
            print("Manual removal succeeded.")
        except Exception as e:
            print(f"Failed to remove installed EXE: {e}")
    else:
        print_step("6a", "No installed EXE found for manual removal.")

def delete_existing_installer():
    installer_path = os.path.join(OUTPUT_FOLDER, INSTALLER_FILENAME)
    print_step(7, f"Checking for existing installer at: {installer_path}")
    if os.path.exists(installer_path):
        try:
            os.remove(installer_path)
            print(f"Deleted existing installer file: {installer_path}")
        except Exception as e:
            print(f"Failed to delete installer file: {e}")

def run_installer_compiler():
    print_step(8, f"Running Inno Setup Compiler on {APP_ISS}")
    iss_dir = os.path.dirname(APP_ISS)
    subprocess.run([ISCC_PATH, APP_ISS], check=True, cwd=iss_dir)
    print("Installer created successfully.")

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            body = f"""
            <html><head><title>LVGL Font Generator Installer</title></head>
            <body>
                <h2>LVGL Font Generator Installer</h2>
                <p><a href="{INSTALLER_FILENAME}">Click here to download the installer</a></p>
            </body></html>
            """
            self.wfile.write(body.encode("utf-8"))
        else:
            super().do_GET()

def serve_installer(folder=OUTPUT_FOLDER):
    if not os.path.exists(folder):
        print(f"Error: Directory to serve does not exist: {folder}")
        sys.exit(1)
    os.chdir(folder)
    handler = CustomHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    url = f"http://localhost:{PORT}/"
    print(f"Serving folder '{folder}' at {url}")
    webbrowser.open(url)

    def serve():
        httpd.serve_forever()
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return httpd

# ==========================================================
# MAIN EXECUTION
# ==========================================================
def main():
    print("\n" + "#" * 60)
    print("===== Starting Automated Build and Installer Script =====")
    print("#" * 60 + "\n")

    if not os.path.exists(APP_PY):
        print(f"Error: Python script not found: {APP_PY}")
        sys.exit(1)
    if not os.path.exists(ICON_FILE):
        print(f"Error: Icon file not found: {ICON_FILE}")
        sys.exit(1)

    # Check and install required Python modules before proceeding
    check_and_install_modules(required_modules)

    check_and_install_pyinstaller()
    check_iscc()

    exe_path = build_exe(ICON_FILE)
    if exe_path is None:
        print("Build failed. Aborting.")
        sys.exit(1)

    dist_exe = os.path.join(DIST_FOLDER, "font2c_lvgl.exe")
    if not os.path.exists(dist_exe):
        print(f"Error: {dist_exe} not found. Build may have failed.")
        sys.exit(1)

    kill_font2c_processes()
    run_uninstaller_and_clean()

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    installer_target = os.path.join(OUTPUT_FOLDER, INSTALLER_FILENAME)
    shutil.copyfile(exe_path, installer_target)

    delete_existing_installer()
    run_installer_compiler()

    httpd = serve_installer()
    input("Press Enter to stop serving and exit...\n")
    httpd.shutdown()

    print("\n" + "#" * 60)
    print("===== Script Completed Successfully =====")
    print("#" * 60 + "\n")

if __name__ == "__main__":
    main()
