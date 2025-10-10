import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont
import os

# Constants
CHAR_START = 32  # Space
CHAR_END = 127   # ASCII printable characters
IMAGE_SIZE = (16, 16)  # Width x Height for each character

# GUI Application
class FontConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TTF to C Array Font Converter")
        self.root.geometry("500x250")

        # UI Elements
        self.label = tk.Label(root, text="Select a TrueType Font (.ttf) file:")
        self.label.pack(pady=10)

        self.font_path_entry = tk.Entry(root, width=50)
        self.font_path_entry.pack(pady=5)

        self.browse_button = tk.Button(root, text="Browse", command=self.browse_ttf)
        self.browse_button.pack(pady=5)

        self.generate_button = tk.Button(root, text="Generate C Array", command=self.generate_c_array)
        self.generate_button.pack(pady=20)

    def browse_ttf(self):
        file_path = filedialog.askopenfilename(filetypes=[("TTF Files", "*.ttf")])
        if file_path:
            self.font_path_entry.delete(0, tk.END)
            self.font_path_entry.insert(0, file_path)

    def generate_c_array(self):
        font_path = self.font_path_entry.get()
        if not font_path or not os.path.isfile(font_path):
            messagebox.showerror("Error", "Please select a valid .ttf file.")
            return

        try:
            font_size = 16
            font = ImageFont.truetype(font_path, font_size)
            output_lines = []

            output_lines.append("unsigned char font_data[] = {\n")

            for char_code in range(CHAR_START, CHAR_END):
                char = chr(char_code)
                img = Image.new("1", IMAGE_SIZE, 0)  # mode '1' = 1-bit pixels
                draw = ImageDraw.Draw(img)
                draw.text((0, 0), char, font=font, fill=1)

                output_lines.append(f"    /* '{char}' ({char_code}) */ ")
                for y in range(img.height):
                    row_byte = 0
                    for x in range(img.width):
                        pixel = img.getpixel((x, y))
                        row_byte = (row_byte << 1) | (1 if pixel else 0)
                    output_lines.append(f"0x{row_byte:02X}, ")
                output_lines.append("\n")

            output_lines.append("};\n")

            # Save to file
            output_filename = "font_data.c"
            with open(output_filename, "w") as f:
                f.writelines(output_lines)

            messagebox.showinfo("Success", f"C array generated as '{output_filename}'.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Run the GUI application
if __name__ == "__main__":
    root = tk.Tk()
    app = FontConverterApp(root)
    root.mainloop()
