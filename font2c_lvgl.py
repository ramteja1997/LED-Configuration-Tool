import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import webbrowser
import freetype


class SingleFontConverter:
    def __init__(self, master, index):
        self.master = master
        self.index = index

        self.frame = tk.Frame(master, relief=tk.RIDGE, bd=2, padx=5, pady=5)
        self.frame.pack(pady=5, fill="x")

        row1 = 0
        tk.Label(self.frame, text=f"Font {index+1} Name:").grid(row=row1, column=0, sticky="e")
        self.name_var = tk.StringVar()
        tk.Entry(self.frame, textvariable=self.name_var, width=20).grid(row=row1, column=1, sticky="w", padx=2)

        tk.Label(self.frame, text="TTF File:").grid(row=row1, column=2, sticky="e")
        self.path_entry = tk.Entry(self.frame, width=50)
        self.path_entry.grid(row=row1, column=3, sticky="w", padx=2)

        self.browse_btn = tk.Button(self.frame, text="Browse", command=self.browse_file)
        self.browse_btn.grid(row=row1, column=4, padx=2)

        row2 = 1
        tk.Label(self.frame, text="Font Size (px):").grid(row=row2, column=0, sticky="e", padx=2, pady=2)
        self.size_var = tk.IntVar(value=16)
        tk.Spinbox(self.frame, from_=8, to=72, textvariable=self.size_var, width=5).grid(row=row2, column=1, sticky="w", padx=2)

        tk.Label(self.frame, text="Bpp:").grid(row=row2, column=2, sticky="e", padx=2, pady=2)
        self.bpp_var = tk.StringVar(value='1')
        ttk.Combobox(self.frame, textvariable=self.bpp_var, values=['1','2','3','4','8'], width=3, state='readonly').grid(row=row2, column=3, sticky="w", padx=2)

        row3 = 2
        tk.Label(self.frame, text="Unicode Range Start (hex):").grid(row=row3, column=0, sticky="e", padx=2, pady=2)
        self.uni_start_var = tk.StringVar(value="20")
        tk.Entry(self.frame, textvariable=self.uni_start_var, width=6).grid(row=row3, column=1, sticky="w", padx=2)

        tk.Label(self.frame, text="Unicode Range End (hex):").grid(row=row3, column=2, sticky="e", padx=2, pady=2)
        self.uni_end_var = tk.StringVar(value="7F")
        tk.Entry(self.frame, textvariable=self.uni_end_var, width=6).grid(row=row3, column=3, sticky="w", padx=2)

        # clickable unicode range link on row 4
        row4 = 3
        link = tk.Label(self.frame, text="Unicode Character Ranges", fg="blue", cursor="hand2")
        link.grid(row=row4, column=0, columnspan=5, sticky="w", padx=2, pady=2)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://jrgraphix.net/research/unicode.php"))

        self.convert_btn = tk.Button(self.frame, text="Generate .c File", command=self.convert_font)
        self.convert_btn.grid(row=row4+1, column=0, columnspan=5, pady=5)

        self.status_label = tk.Label(self.frame, text="", fg="green")
        self.status_label.grid(row=row4+2, column=0, columnspan=5, sticky="w", padx=2)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("TTF Font Files", "*.ttf")])
        if filename:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, filename)
            self.status_label.config(text="")

    def get_unique_filename(self, path):
        base, ext = os.path.splitext(path)
        counter = 1
        candidate = path
        while os.path.exists(candidate):
            candidate = f"{base}({counter}){ext}"
            counter += 1
        return candidate

    def convert_font(self):
        font_path = self.path_entry.get()
        font_name = self.name_var.get().strip()
        if not font_name:
            messagebox.showerror("Error", "Please enter the font name.")
            return

        if not os.path.isfile(font_path):
            messagebox.showerror("Error", f"Please select a valid TTF font file for {font_name}.")
            return

        try:
            size = int(self.size_var.get())
            bpp = int(self.bpp_var.get())
            uni_start = int(self.uni_start_var.get(), 16)
            uni_end = int(self.uni_end_var.get(), 16)
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input data: {e}")
            return

        self.status_label.config(text="Processing...")
        self.master.update()

        try:
            output_filename = self.generate_lvgl_font_c(font_path, font_name, size, bpp, uni_start, uni_end)
            self.status_label.config(text=f"Success: {os.path.basename(output_filename)}")
            messagebox.showinfo("Success", f"Generated LVGL font C file:\n{output_filename}")
        except Exception as e:
            self.status_label.config(text="Error")
            messagebox.showerror("Error", f"Failed to generate font:\n{e}")

    def write_glyph_bitmap_comment(self, f, char_code):
        ch = chr(char_code)
        if ch == '"':
            ch = '\\"'
        elif ch == '\\':
            ch = '\\\\'
        f.write(f"\n/* U+{char_code:04X} \"{ch}\" */\n\n")

    def generate_lvgl_font_c(self, font_path, font_name, size, bpp, start, end):
        face = freetype.Face(font_path)
        face.set_pixel_sizes(0, size)

        base_name = font_name
        initial_path = os.path.join(os.path.dirname(font_path), f"{base_name}.c")
        output_filename = self.get_unique_filename(initial_path)

        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(f"/*******************************************************************************\n\n")
            f.write(f"* Size: {size} px\n\n* Bpp: {bpp}\n\n")
            f.write(f"* Opts: --font {font_path} --size {size} --bpp {bpp} --no-compress --format lvgl\n\n")
            f.write(f"*******************************************************************************/\n\n")

            f.write("#ifdef LV_LVGL_H_INCLUDE_SIMPLE\n\n#include \"lvgl.h\"\n\n#else\n\n#include \"lvgl/lvgl.h\"\n\n#endif\n\n")

            macro_name = base_name.upper().replace(" ", "_").replace("-", "_")
            f.write(f"#ifndef {macro_name}\n#define {macro_name} 1\n\n#endif\n\n")

            f.write("/*-----------------\n\n* BITMAPS\n\n*----------------*/\n\n")
            f.write("/*Store the image of the glyphs*/\n\n")
            f.write("static LV_ATTRIBUTE_LARGE_CONST const uint8_t glyph_bitmap[] = {\n")

            for code in range(start, end + 1):
                try:
                    face.load_char(chr(code), freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
                except:
                    continue

                bmp = face.glyph.bitmap
                width = bmp.width
                rows = bmp.rows
                buffer = bmp.buffer

                self.write_glyph_bitmap_comment(f, code)

                row_bytes = (width + 7) // 8 if width != 0 else 0

                for y in range(rows):
                    f.write("    ")
                    for b in range(row_bytes):
                        idx = y * row_bytes + b
                        if idx < len(buffer):
                            f.write(f"0x{buffer[idx]:02X}")
                        else:
                            f.write("0x00")
                        if not (y == rows -1 and b == row_bytes -1):
                            f.write(", ")
                    f.write(",\n")

            f.write("};\n\n")
            f.write(f"#endif /* {macro_name} */\n")

        return output_filename


class LVGLFontConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LVGL Multi Font Converter")
        self.root.geometry("950x700")

        # ---------- Scrollable Canvas ----------
        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # add font converters inside scrollable frame
        for i in range(5):
            SingleFontConverter(self.scrollable_frame, i)


if __name__ == "__main__":
    root = tk.Tk()
    app = LVGLFontConverterApp(root)
    root.mainloop()
