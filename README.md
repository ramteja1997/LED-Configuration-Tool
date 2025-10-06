
This script/project provides a graphical user interface (GUI) to convert multiple TrueType font (TTF) files into C source code files compatible with LVGL embedded graphics library.

### Key functions and classes:

- **`SingleFontConverter` class**  
  Manages one font conversion widget allowing the user to:  
  - Enter font name  
  - Select a TTF file using a file dialog  
  - Specify font size in pixels and bits per pixel (bpp)  
  - Define Unicode range (start and end in hex)  
  - Generate the corresponding `.c` font source file using FreeType rendering  

- **`convert_font` method**  
  Validates inputs, processes the TTF font via FreeType, and creates the LVGL-compatible `.c` file with bitmap glyph data and necessary headers.

- **`generate_lvgl_font_c` method**  
  Core logic that loads each glyph bitmap within the Unicode range, formats it into a C array, and writes complete LVGL font source code to file.

- **`LVGLFontConverterApp` class**  
  Creates the main application window with a scrollable canvas to hold multiple `SingleFontConverter` instances (up to 5 by default).  
  Also handles mouse wheel (vertical and horizontal) scrolling support for ease of navigation.

***

### Usage

Run the script to open the GUI. For each font converter widget:  
- Enter a font name  
- Browse and select the `.ttf` font file  
- Adjust font size, bpp, and Unicode range  
- Click "Generate .c File" to output the LVGL font source C file alongside the TTF file

This tool simplifies generating multiple embedded fonts for LVGL projects efficiently in one unified interface.


#  build_and_installer.py script

## Automated Build and Installer Script

This Python script automates the building and packaging process of the LVGL Font Generator application.

### What each function does:

- **`check_and_install_pyinstaller()`**  
  Checks if PyInstaller is installed; if missing, installs it via pip.

- **`check_iscc()`**  
  Verifies the presence of Inno Setup Compiler (`ISCC.exe`) to compile the installer.

- **`delete_existing_exe(exe_name)`**  
  Deletes any previously built executable from the `dist` folder to ensure a clean build.

- **`build_exe(icon_path)`**  
  Uses PyInstaller to build a one-file, windowed executable of the Python app with the specified icon.

- **`run_uninstaller()`**  
  Attempts to uninstall any existing installed application: runs Inno Setup uninstaller if found or manually deletes the installed executable.

- **`delete_existing_installer()`**  
  Deletes any existing installer executable in the output folder (`LVGLFontGenerator_Installer.exe`) to avoid conflicts.

- **`run_installer()`**  
  Runs the Inno Setup Compiler to generate a new installer executable from the `.iss` script.

- **`main()`**  
  Controls the workflow: checks prerequisites, builds the executable, uninstalls old app, deletes old installer, then builds new installer with clear step-by-step console output.

***

### Usage

Run this script after placing your `.py`, `.ico`, and `.iss` files in their appropriate locations. It ensures automatic building, clean upgrade uninstallations, and installer generation for distribution on Windows systems.
