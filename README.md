# LED-Font-Converter

LED-Font-Converter is a desktop graphical application designed for converting TrueType font (TTF) files into C source code files compatible with the LVGL (Light and Versatile Graphics Library) embedded graphics library. This project simplifies the process of generating custom fonts for embedded systems by allowing users to specify font properties such as size, bits per pixel (bpp), and Unicode ranges, all via an easy-to-use interface.

---

## Features

- **Multiple Font Conversion Widgets:** Convert multiple fonts simultaneously (default support up to 5 fonts).
- **Customizable Font Parameters:** Specify font name, size (in pixels), bits per pixel (quality), and Unicode range (start and end in hex).
- **Automated Glyph Rendering:** Uses FreeType library bindings to render precise glyph bitmaps for the specified Unicode ranges.
- **LVGL-Compatible Output:** Generates complete `.c` source files with glyph bitmaps and metadata formatted to LVGL's font API.
- **Batch Processing:** Enable efficient font development for complex embedded applications.
- **Build and Packaging Automation:** Provided build scripts automate creation of standalone Windows executables and professional installers.
- **Installer Support:** Uses Inno Setup to create a user-friendly installation experience including custom icons and uninstall functionality.

---

## Prerequisites and Dependencies

### Software Requirements

- **Operating System:** Windows 10 or later recommended for building and running the packaged app.
- **Python:** Version 3.7 or higher.
- **Node.js (optional):** Version 14+ required if using LVGL’s `lv_font_conv` command-line conversions.
- **Inno Setup Compiler (ISCC.exe):** Required for building Windows installers.

### Python Libraries

Install via `pip install` or use the provided `requirements.txt`:

- `freetype-py` — Python bindings for FreeType to render TTF glyphs.
- `PyQt5` — Provides the GUI framework.
- `Pillow` — Image processing for bitmap manipulation.
- `PyInstaller` — Used for packaging the Python app as an executable.
- `setuptools` and `wheel` — For Python packaging utilities.

---

## Installation and Setup

1. **Clone the repository:**
git clone https://github.com/ramteja1997/LED-Font-Converter.git
cd LED-Font-Converter

text

2. **Install Python dependencies:**
pip install -r requirements.txt

text

3. **Install Node.js and Inno Setup Compiler:**
- Download and install Node.js from the official website if you plan to use LVGL CLI tools.
- Download Inno Setup Compiler from [jrsoftware.org](https://jrsoftware.org/isinfo.php) for generating Windows installers.

---

## Usage Guide

### Running the Application

Launch the main GUI application to start converting fonts:

python main.py

text

### Using the Font Converter GUI

- **Add Fonts:** Up to five font conversion widgets are available.
- **Font Name:** Enter a descriptive name for the font output.
- **Select TTF Font:** Browse and select the TTF file from disk.
- **Font Size (Pixels):** Specify the height of glyphs.
- **Bits Per Pixel (BPP):** Choose between 1, 2, 4, or 8 bpp for glyph quality and anti-aliasing.
- **Unicode Range:** Enter hexadecimal Unicode start and end points to limit conversion to required glyphs.
- **Generate C File:** Click the button to generate the LVGL-compatible `.c` font source.

The generated `.c` file will be saved alongside the original TTF file, with automatic file renaming to avoid overwrites.

---

## How It Works: Internal Workflow

1. **Font Loading:**
   - The selected TTF font is loaded via FreeType bindings (`freetype-py`).
   - Font size and rendering parameters are set.

2. **Glyph Rendering:**
   - For each Unicode character in the selected range, a glyph bitmap is rendered.
   - The bitmap data is extracted and stored.

3. **Source Code Generation:**
   - Bitmap arrays and glyph descriptors are formatted as C arrays.
   - Full LVGL font structures including metadata are generated.
   - The final font `.c` file is saved.

---

## Building Executable & Installer

### Using the Build Script

Run the build and installer script to package the application into a single executable and an installer:

python build_and_installer.py

text

- **PyInstaller Integration:**
  - Compiles Python scripts into a single Windows executable.
  - Applies the custom application icon.
  - Cleans previous builds to ensure fresh packaging.

- **Inno Setup Installer Creation:**
  - Runs the Inno Setup Compiler on the included `.iss` script.
  - Creates a Windows installer `.exe` with uninstall support.
  - Ensures old installations are properly removed before new installation.

---

## Project Structure

LED-Font-Converter/
│
├── main.py # Main application entry point (GUI launcher)
├── SingleFontConverter.py # Font conversion widget and logic
├── build_and_installer.py # Automation script for building and packaging
├── installer_script.iss # Inno Setup script for installer configuration
├── requirements.txt # List of Python dependencies
├── resources/ # Icons and auxiliary resources
└── README.md # Project documentation (this file)

text

---

## Troubleshooting

- Ensure all dependencies are correctly installed, especially Python libraries.
- For building, verify that Inno Setup Compiler is installed and accessible on PATH.
- Check that the Unicode ranges you specify are valid and supported by the TTF font.
- If font conversion fails, verify that the TTF file is valid and not corrupted.

---

## Contribution

Contributions are welcome! Please fork the repo and submit pull requests for fixes or new features. Open issues for suggestions or bugs.

---

## License

This project is licensed under the MIT License.

---

## Contact

For support or questions, please open an issue on GitHub or contact the maintainers through the repository.

---
