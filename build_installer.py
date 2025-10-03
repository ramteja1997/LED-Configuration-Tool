import subprocess
import os
import sys

# Configurations:
PYINSTALLER = "pyinstaller"
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"  # update if necessary
APP_PY = "font2c_lvgl.py"
APP_ISS = "Setup.iss"
ICON_FILE = "LVGL_FontGen.ico"  # icon file path can be relative or absolute
DIST_FOLDER = "dist"

# Installer output folder and filename (no subfolder here)
OUTPUT_FOLDER = r"C:\Users\Kushal\PycharmProjects\LED-Font-Converter\Output"
INSTALLER_FILENAME = "LVGLFontGenerator_Installer.exe"

# Default install directory from your .iss's DefaultDirName setting (update if different)
#INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "LVGLFontGenerator")
INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "LVGLFontGenerator")



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
    print_step(2, "Checking for Inno Setup Compiler at expected path...")
    if not os.path.exists(ISCC_PATH):
        print(f"Error: Inno Setup Compiler not found at {ISCC_PATH}. Please install it to proceed.")
        sys.exit(1)
    else:
        print("Inno Setup Compiler found.")


def delete_existing_exe(exe_name):
    exe_path = os.path.join(DIST_FOLDER, exe_name)
    if os.path.exists(exe_path):
        print_step(3, f"Deleting existing EXE if present: {exe_path}")
        os.remove(exe_path)
    else:
        print_step(3, f"No existing EXE to delete at {exe_path}")
    return exe_path


def build_exe(icon_path):
    exe_name = os.path.basename(APP_PY).replace(".py", ".exe")
    exe_path = delete_existing_exe(exe_name)

    print_step(4, f"Building the executable: {exe_name}")
    print(f"Command:\npyinstaller --onefile --windowed --icon={icon_path} {APP_PY}")
    cmd = [
        PYINSTALLER,
        "--onefile",
        "--windowed",
        f"--icon={icon_path}",
        APP_PY,
        f"--distpath={DIST_FOLDER}",
        "--clean"
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with exit code {e.returncode}")
        return None

    if not os.path.exists(exe_path):
        print(f"Error: EXE {exe_path} not created!")
        return None

    print(f"Executable built successfully at {exe_path}\n")
    return exe_path


def run_uninstaller():
    # First try to run the uninstaller if it exists (for installed app)
    uninstaller_path = os.path.join(INSTALL_DIR, "unins000.exe")
    if os.path.exists(uninstaller_path):
        print_step(5, f"Found uninstaller at: {uninstaller_path}. Running uninstall...")
        try:
            subprocess.run([uninstaller_path, "/VERYSILENT", "/NORESTART"], check=True)
            print("Uninstallation completed successfully.")
            return
        except subprocess.CalledProcessError as e:
            print(f"Uninstaller failed with exit code {e.returncode}, proceeding with manual removal...")

    # If no uninstaller or uninstall fails, try to delete installed exe manually
    installed_exe = os.path.join(INSTALL_DIR, "font2c_lvgl.exe")
    if os.path.exists(installed_exe):
        print_step("5a", f"No uninstaller found. Deleting installed EXE manually: {installed_exe}")
        try:
            os.remove(installed_exe)
            print("Manual removal of installed EXE completed.")
        except Exception as ex:
            print(f"Failed to delete installed EXE: {ex}")
    else:
        print_step("5a", "No installed EXE found for manual removal. Skipping uninstall step.")


def delete_existing_installer():
    installer_path = os.path.join(OUTPUT_FOLDER, INSTALLER_FILENAME)
    print_step("5b", f"Checking for existing installer at: {installer_path}")
    if os.path.exists(installer_path):
        try:
            os.remove(installer_path)
            print(f"Deleted existing installer file: {installer_path}")
        except Exception as e:
            print(f"Failed to delete existing installer: {e}")
    else:
        print("No existing installer found in output folder.")


def run_installer():
    print_step(6, f"Running Inno Setup Compiler to build installer from {APP_ISS}")
    try:
        subprocess.run([ISCC_PATH, APP_ISS], check=True)
        print("Installer created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Inno Setup Compiler failed with exit code {e.returncode}")
        sys.exit(1)


def main():
    print("\n" + "#" * 60)
    print("===== Starting Automated Build and Installer Script =====")
    print("#" * 60 + "\n")

    if not os.path.exists(APP_PY):
        print(f"Error: Python script {APP_PY} not found!")
        sys.exit(1)

    if not os.path.exists(ICON_FILE):
        print(f"Error: Icon file not found: {ICON_FILE}")
        sys.exit(1)

    check_and_install_pyinstaller()
    check_iscc()

    exe_path = build_exe(ICON_FILE)
    if exe_path is None:
        print("Build failed. Aborting.")
        sys.exit(1)

    # Uninstall installed app or delete installed exe
    run_uninstaller()
    # Delete existing installer executable file in output folder
    delete_existing_installer()
    # Run Inno Setup compiler to create new installer
    run_installer()

    print("\n" + "#" * 60)
    print("===== Script Completed Successfully =====")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
